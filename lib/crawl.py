#!/usr/bin/python
#
# The crawler
#	- read xml config
#	- build crawler path from config
#	- follow each feed_url to completion, save page
#	- cache all visited urls

from xml.dom.minidom import parse
import logging
import logging.handlers
import urlparse
import re

log = logging.getLogger("Crawler")
log.addHandler(logging.StreamHandler())

class AbstractPathObject(object):
	"""
	The common base class for path objects.
	"""
	url = None

	def setUrl(self, dom_node, parent_url):
		self.url = dom_node.getAttribute("value")
		if dom_node.hasAttribute("relative") and bool(dom_node.getAttribute("relative")):
			if not parent_url:
				log.critical("Could not build relative url without a parent_url. Failed to build Feed %s." % (self.url))
				return None

			self.url = urlparse.urljoin(parent_url, self.url)
			log.debug("Built absolute url %s." % (self.url))


class AbstractPathRegexObject(object):
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
		self.setUrl(dom_node, parent_url)
		if not self.url:
			return None

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


class Target(AbstractPathObject):
	"""
	Base class for target urls, that should be saved.
	"""
	def __init__(self, dom_node, parent_url=None):
		self.setUrl(dom_node, parent_url)
		if not self.url:
			return None

class TargetRegex(AbstractPathRegexObject, Target):
	"""
	A target url based on a url.
	"""

	def __init__(self, dom_node, parent_url=None):
		super(TargetRegex, self).__init__(dom_node, parent_url)
		self.setPattern(self.url)
		self.setMaxMatches(dom_node)

class TargetUrl(Target):
	pass

class FeedUrl(Feed):
	pass

class FeedRegex(AbstractPathRegexObject, Feed):
	"""
	A feed based on a regex of a url.
	"""

	def __init__(self, dom_node, parent_url=None):
		super(FeedRegex, self).__init__(dom_node, parent_url)
		self.setPattern(self.url)
		self.setMaxMatches(dom_node)
		

class Crawler:
	"""
	The web crawler.
	"""
	name = "unknown"

	feed_list = []

	def __init__(self, dom_config, log_level=logging.WARNING):
		" Setup the Crawler, load the config "
		log.setLevel(log_level)
		log.info("Configuring crawler...")
		self.build_crawler_from_dom(dom_config)
		

	def build_crawler_from_dom(self, dom):
		# Crawler path
		path = dom.getElementsByTagName("path")[0]
		self.name = path.getAttribute("name")
		log.info("Crawler path named '%s'." % self.name)

		for node in path.childNodes:
			if node.nodeType == node.ELEMENT_NODE:
				log.debug("Node: %s of type %s" % (node.nodeName, node.nodeType))
				if node.nodeName != 'feed_url':
					log.warning("Unknown tag %s, skipping it." % (node.nodeName))
					continue
				
				self.feed_list.append(FeedUrl(node))
			
		

	def start(self):
		log.info("Starting crawl %s ..." % (self.name))


if __name__ == "__main__":
	import sys
	if len(sys.argv) < 2:
		sys.stderr.write("""Missing config file\nUsage:
		%s <config_file>\n""" % sys.argv[0])
		sys.exit(2)
		
	dom = parse(sys.argv[1])
	crawler = Crawler(dom.getElementsByTagName("crawler")[0], logging.DEBUG)
	crawler.start()
