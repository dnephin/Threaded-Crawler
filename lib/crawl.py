#!/usr/bin/python
#
# The crawler
#	- read xml config
#	- build crawler path from config
#	- follow each feed_url to completion, save page
#	- cache all visited urls

# NOTE: regex for path objects can not be in diretory or domain, only file
# TODO: add time of each request
# TODO: what happens when pages 404 or 500 ? catch exceptions ?

from xml.dom.minidom import parse
import logging
import logging.handlers
import urlparse
import re
import urllib2
import cookielib

log = logging.getLogger("Crawler")
log.addHandler(logging.StreamHandler())

class Agent(object):
	"""
	A singleton class used by feed objects to access pages, and store the results.
	"""
	__instance = None

	class __impl:
		target_saver = None
		opener = None
		setup = False # TODO: check for setup agent
		url_cache = []

		def setup(self, dom_node):
			# TODO: setup proxy from config

			cookiejar = cookielib.CookieJar()
			self.opener = urllib2.build_opener(
				urllib2.HTTPCookieProcessor(cookiejar))

			target_saver_node = dom_node.getElementsByTagName("target_save")[0]
			class_name = target_saver_node.getAttribute("class")
			module_name = target_saver_node.getAttribute("module")
			self.target_saver = getattr(__import__(module_name), class_name)() # TODO: fix this to work with any module

		def fetch(self, url):
			"""
			Open the url, check for valid response and return page url and page.
			Stores the url in the url_cache.
			"""
			if url in self.url_cache:
				log.warning("url %s already in cache, skipping..." % (url))
				return None

			log.info("Fetching %s." % (url))
			resp = self.opener.open(url)

			new_url = resp.geturl()
			self.url_cache.append(new_url)
			if new_url != url:
				self.url__cache.append(url)

			return new_url, unicode(resp.read(), errors='ignore')
			

	def __init__(self):
		if Agent.__instance is None:
			Agent.__instance = Agent.__impl()
	
		self.__dict__['_Agent__instance'] = Agent.__instance

	def __getattr__(self, attr):
		""" Delegate access to implementation """
		return getattr(self.__instance, attr)

	def __setattr__(self, attr, value):
		""" Delegate access to implementation """
		return setattr(self.__instance, attr, value)


class AbstractPathObject(object):
	"""
	The common base class for path objects.
	"""
	orig_url = None
	url = None
	agent = Agent()
	relative = False

	def __init__(self, dom_node, parent_url):
		self.orig_url = dom_node.getAttribute("value")
		if dom_node.hasAttribute("relative") and bool(dom_node.getAttribute("relative")):
			relative = True

			self.url = urlparse.urljoin(parent_url, self.url)
			log.debug("Built absolute url %s." % (self.url))
		else:
			self.url = self.orig_url


	def process(self):
		raise NotImplementedError("This is abstract, no implemented in %s" % (self.__class__.__name__))
		

class AbstractPathRegexObject(AbstractPathObject):
	"""
	Abstract base class for path objects that are regex patterns.
	"""
	max_matches = 0
	regex_pattern = None

	def setMaxMatches(self, dom_node):
		if dom_node.hasAttribute("max_matches"):
			self.max_matches = dom_node.getAttribute("max_matches")

	def setPattern(self, url):
		self.regex_pattern = re.compile(url)

	def findUrls(self, page):
		match_list = []
		# TODO: skip some of the <head> data? parse page first maybe?
		log.debug("Finding urls on page for regex %s on page" % (self.regex_pattern.pattern))
		for line in page.split("\n"):
			m = self.regex_pattern.search(line)
			if m:
				if self.relative:
					target_url = urlparse.urljoin(self.url, m.group(0))
				else:
					target_url = m.group(0)
				match_list.append(target_url) 
				log.debug("Adding url %s for the page." % (target_url))
		return match_list


class Feed(AbstractPathObject):
	"""
	Base class for urls to follow that have links to Targets or other Feeds.
	"""
	feed_url_list = []
	feed_regex_list = []
	target_regex_list = []
	target_url_list = []
	max_depth = 0

	def __init__(self, dom_node, parent_url=None):
		super(Feed, self).__init__(dom_node, parent_url)
		if dom_node.hasAttribute("max_depth"):
			self.max_depth = dom_node.getAttribute("max_depth")
		
		for node in dom_node.childNodes:
			if node.nodeType == node.ELEMENT_NODE:
				log.debug("Node: %s of type %s" % (node.nodeName, node.nodeType))
				if node.nodeName == 'feed_url':
					self.feed_url_list.append(FeedUrl(node, self.url))
				elif node.nodeName == 'feed_regex':
					self.feed_regex_list.append(FeedRegex(node, self.url))
				elif node.nodeName == 'target_regex':
					self.target_regex_list.append(TargetRegex(node, self.url))
				elif node.nodeName == 'target_url':
					self.target_url_list.append(TargetUrl(node, self.url))
				else:
					log.warning("Unknown tag %s, skipping it." % (node.nodeName))
					continue

	def processLists(self, page):
		for target_url in self.target_url_list:
			target_url.process()
		for target_regex in self.target_regex_list:
			target_regex.process(page)
		for feed_url in self.feed_url_list:
			feed_url.process()
		for feed_regex in self.feed_regex_list:
			feed_regex.process(page)

class Target(AbstractPathObject):
	pass

class TargetRegex(AbstractPathRegexObject, Target):
	def __init__(self, dom_node, parent_url=None):
		super(TargetRegex, self).__init__(dom_node, parent_url)
		self.setPattern(self.orig_url)
		self.setMaxMatches(dom_node)

	def process(self, page):
		for target_url in self.findUrls(page):
			final_url, page = self.agent.fetch(self.url)
			self.agent.target_saver.save(final_url, page)
			

class TargetUrl(Target):
	def __init__(self, dom_node, parent_url=None):
		super(TargetUrl, self).__init__(dom_node, parent_url)

	def process(self):
		final_url, page = self.agent.fetch(self.url)
		self.agent.target_saver.save(final_url, page)

class FeedRegex(AbstractPathRegexObject, Feed):
	def __init__(self, dom_node, parent_url=None):
		super(FeedRegex, self).__init__(dom_node, parent_url)
		self.setPattern(self.orig_url)
		self.setMaxMatches(dom_node)

	def process(self, page):
		for target_url in self.findUrls(page):
			final_url, page = self.agent.fetch(target_url)
			self.processLists(page)
	
class FeedUrl(Feed):
	def __init__(self, dom_node, parent_url=None):
		super(FeedUrl, self).__init__(dom_node, parent_url)

	def process(self):
		final_url, page = self.agent.fetch(self.url)
		self.processLists(page)

class Crawler(object):
	"""
	The web crawler.
	"""
	name = "unknown"

	feed_list = []
	target_list = []
	

	def __init__(self, dom_config, log_level=logging.WARNING):
		" Setup the Crawler, load the config "
		log.setLevel(log_level)
		log.info("Configuring crawler...")
		self.build_crawler_from_dom(dom_config)

		# setup agent
		self.agent = Agent()
		self.agent.setup(dom_config.getElementsByTagName("agent")[0])


	def build_crawler_from_dom(self, dom):
		# Crawler path
		path = dom.getElementsByTagName("path")[0]
		self.name = path.getAttribute("name")
		log.info("Crawler path named '%s'." % self.name)

		for node in path.childNodes:
			if node.nodeType == node.ELEMENT_NODE:
				log.debug("Node: %s of type %s" % (node.nodeName, node.nodeType))
				
				if node.nodeName == 'feed_url':
					self.feed_list.append(FeedUrl(node))
				elif node.nodeName == 'target_url':
					self.target_list.appened(TargetUrl(node))
				else:
					log.warning("Unknown tag %s, skipping it." % (node.nodeName))
					continue
			
	def start(self):
		log.info("Starting crawl %s ..." % (self.name))
		for target in self.target_list:
			target.process()
		for feed in self.feed_list:
			feed.process()
		log.info("Visited Pages:\n%s", "\n".join(self.agent.url_cache))
		


if __name__ == "__main__":
	import sys
	if len(sys.argv) < 2:
		sys.stderr.write("""Missing config file\nUsage:
		%s <config_file>\n""" % sys.argv[0])
		sys.exit(2)
		
	dom = parse(sys.argv[1])
	crawler = Crawler(dom.getElementsByTagName("crawler")[0], logging.DEBUG)
	crawler.start()
