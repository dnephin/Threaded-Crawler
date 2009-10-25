#!/usr/bin/python
#
# The crawler
#	- read xml config
#	- build crawler path from config
#	- follow each feed_url to completion, call save method of target_saver

# NOTE: regex for path objects can not be in diretory or domain, only file

# TODO: implement max_depth

from xml.dom.minidom import parse
import logging
import logging.handlers
import urlparse
import re
import urllib2
import cookielib
import time
import random

# logger for crawler module
log = logging.getLogger("Crawler")
log.addHandler(logging.StreamHandler())


class BrokenPathException(Exception):
	" Exception thrown when a path reached its end because of an HTTP error "
	def __init__(self, url, code, msg):
		self.url = url
		self.code = code
		self.msg = msg
		
	def __str__(self):
			return "%d: %s (%s)" % (self.code, self.msg, self.url)


class AgentHttpErrorHandler(urllib2.HTTPDefaultErrorHandler):
	" Http exception handler for 4xx, 5xx error codes "
	def __init__(self):
		pass
	
	def http_error_default(self, req, fp, code, msg, hdrs):
		log.warning("Error fetching %s: %d, %s" % (req.get_full_url(), code, msg))
		raise BrokenPathException(req.get_full_url(), code, msg)
		

class Agent(object):
	"""
	A singleton class used by feed objects to:
	 - access pages
	 - store the target pages
	 - randomly sleep before accessing pages
	"""
	__instance = None

	class __impl:
		target_saver = None
		opener = None
		is_setup = False
		url_cache = []
		min_sleep = 0
		max_sleep = 0

		def setup(self, dom_node):
			" Setup the Agent "
			# opener setup
			proxy_handler = urllib2.BaseHandler
			proxy_tags = dom_node.getElementsByTagName("proxy")
			if proxy_tags and len(proxy_tags):
				proxy_url = proxy_tags[0].getAttribute("url")
				proxy_handler = urllib2.ProxyHandler({'http': proxy_url})
				log.info("Setup Agent Proxy: %s" % (proxy_url))
				
			error_handler = AgentHttpErrorHandler()
				
			cookiejar = cookielib.CookieJar()
			self.opener = urllib2.build_opener(
				urllib2.HTTPCookieProcessor(cookiejar),
				proxy_handler,
				error_handler)

			# target saver setup
			target_saver_node = dom_node.getElementsByTagName("target_save")[0]
			class_name = target_saver_node.getAttribute("class")
			module_name = target_saver_node.getAttribute("module")
			self.target_saver = getattr(__import__(module_name), class_name)()
			log.info("Setup Agent target saver class: %s.%s" % (module_name, class_name))
			
			# sleeper setup
			random.seed(time.time())
			sleep_tag = dom_node.getElementsByTagName("sleep_per_fetch")[0]
			self.min_sleep = float(sleep_tag.getAttribute("min_seconds"))
			self.max_sleep = float(sleep_tag.getAttribute("max_seconds"))
			log.info("Setup Agent random sleep with values %1.2f to %1.2f" % (self.min_sleep, self.max_sleep))
			
			self.is_setup = True

		def fetch(self, url):
			" Open the url, check for valid response and return page url and page. "
			
			if not self.is_setup:
				raise RuntimeError("Agent must be setup before it is used")

			if url in self.url_cache:
				log.warning("url %s already was already visited, possible recursion..." % (url))

			if self.max_sleep:
				time.sleep(random.uniform(self.min_sleep, self.max_sleep))
				
			log.info("Fetching %s." % (url))
			self.url_cache.append(url)
			start_time = time.time()
			resp = self.opener.open(url)
			run_time = time.time() - start_time
			log.info("Fetched in %2.2f seconds" % (run_time))

			new_url = resp.geturl()
			if new_url != url:
				self.url_cache.append(new_url)

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
	"""  The common base class for path objects. """
	orig_url = None
	url = None
	agent = Agent()

	def __init__(self, dom_node, parent_url):
		self.orig_url = dom_node.getAttribute("value")
		if parent_url:
			self.url = urlparse.urljoin(parent_url, self.url)
			log.debug("Built absolute url %s." % (self.url))
		else:
			self.url = self.orig_url

	def process(self):
		raise NotImplementedError("This is abstract, not implemented in %s" % (self.__class__.__name__))
		

class AbstractPathRegexObject(AbstractPathObject):
	""" Abstract base class for path objects that are regex patterns. """
	max_matches = 0
	regex_pattern = None

	def setMaxMatches(self, dom_node):
		if dom_node.hasAttribute("max_matches"):
			self.max_matches = int(dom_node.getAttribute("max_matches"))
			log.debug("Set max matches to %d." % (self.max_matches))

	def setPattern(self, url):
		self.regex_pattern = re.compile(url)

	def findUrls(self, page):
		match_list = []
		log.debug("Finding urls on page for regex %s" % (self.regex_pattern.pattern))
		for line in page.split("\n"):
			m = self.regex_pattern.search(line)
			if m:
				target_url = urlparse.urljoin(self.url, m.group(0))
				match_list.append(target_url) 
				log.debug("Adding url %s for the page." % (target_url))
			if self.max_matches and len(match_list) >= self.max_matches:
				break
		return match_list


class Feed(AbstractPathObject):
	"""
	Base class for urls to follow that have links to Targets or other Feeds.
	"""
	feed_url_list = []
	feed_regex_list = []
	target_regex_list = []
	target_url_list = []

	def __init__(self, dom_node, parent_url=None):
		super(Feed, self).__init__(dom_node, parent_url)
		
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
			try:
				final_url, page = self.agent.fetch(target_url)
			except BrokenPathException:
				continue
			self.agent.target_saver.save(final_url, page)
			

class TargetUrl(Target):
	def __init__(self, dom_node, parent_url=None):
		super(TargetUrl, self).__init__(dom_node, parent_url)

	def process(self):
		try:
			final_url, page = self.agent.fetch(self.url)	
		except BrokenPathException:
				return
		self.agent.target_saver.save(final_url, page)


class FeedRegex(AbstractPathRegexObject, Feed):
	max_depth = 0

	def __init__(self, dom_node, parent_url=None):
		super(FeedRegex, self).__init__(dom_node, parent_url)
		self.setPattern(self.orig_url)
		self.setMaxMatches(dom_node)
		if dom_node.hasAttribute("max_depth"):
			self.max_depth = int(dom_node.getAttribute("max_depth"))

	def process(self, page, depth=0):
		for target_url in self.findUrls(page):
			try:
				final_url, target_page = self.agent.fetch(target_url)
			except BrokenPathException:
				continue
			self.processLists(target_page)

			# recurse max_depth times
			if self.max_depth and depth < max_depth:
				self.process(target_page, depth+1)
		log.info("Completed feed %s." % (self.orig_url))

	
class FeedUrl(Feed):
	def __init__(self, dom_node, parent_url=None):
		super(FeedUrl, self).__init__(dom_node, parent_url)

	def process(self):
		try:
			final_url, page = self.agent.fetch(self.url)
		except BrokenPathException:
				return
		self.processLists(page)
		log.info("Completed feed %s." % (self.url))

class Crawler(object):
	""" The web crawler. """
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
					self.target_list.append(TargetUrl(node))
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
