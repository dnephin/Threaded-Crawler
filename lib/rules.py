"""
 Rules for which url to follow, and which content to save to disk.
"""

import logging
import random
import ImageFile
import urlparse
import os
from BeautifulSoup import BeautifulSoup
from dto import QueueItem

log = logging.getLogger("ThreadedCrawler")

class Rule(object):
	"""
	An interface for rules that directs the crawler by determining which paths to
	follow and what content to save.
	"""
	def __init__(self, config):
		" configure the rule "
		self.config = config

	def process(self, resp_item):
		" process the ResponseItem, and return a list of any new QueueItems "
		return None


# TODO: load specifics of rules from config file

# TODO: Create a mixin to skip already queued/processed urls, thread safe cache

# TODO: split this into two rules, with a common base class HtmlPage for testing if this is an html page
class HtmlPageImageLinksRule(Rule):
	" Process an html page "

	def process(self, resp_item):
		from_tag = resp_item.qitem.from_tag
		if from_tag != None and from_tag.lower() != 'a':
			log.debug("Skipping, %s not from an anchor tag(<a>)" % resp_item)
			return None
		recurse = resp_item.qitem.recurse_level
		qitems = []
		content = BeautifulSoup(resp_item.content)
		if recurse > 0:
			qitems += self.parse_pages(recurse-1, content, resp_item.response, 
					resp_item.qitem.site_name)

		qitems += self.parse_content(content, resp_item.response, 
				resp_item.qitem.site_name)
		return qitems


	def parse_pages(self, recurse_level, content, resp, name):
		" Parse the html page for more pages "
		qitems = []
		url = resp.geturl()
		a_tags = content.findAll('a')
		log.info("Found %d a tags for '%s'" % (len(a_tags), url))
		for a_tag in a_tags:
			# makes sure it contains an image
			img_tags = a_tag.findAll('img')
			if len(img_tags) != 1:
				continue
			try:
				full_url = urlparse.urljoin(url, a_tag['href'])
			except KeyError, err:
				log.warn("No href tag for %s:%s" % (a_tag, err))
				continue

			qitem = QueueItem(full_url, recurse_level, name, from_tag='a')
			log.debug("adding %s to queue" % qitem)
			qitems.append(qitem)
		return qitems


	def parse_content(self, content, resp, name):
		" Parse the html page for image content "
		url = resp.geturl()
		img_tags = content.findAll('img')
		log.info("Found %d img tags for '%s'" % (len(img_tags), url))
		qitems = []
		for img_tag in img_tags:
			# exclude unlikely images
			img_src = img_tag['src']
			if img_src[-4:] == '.gif':
				continue
			img_url = urlparse.urljoin(url, img_src)

			qitem = QueueItem(img_url, site_name=name, from_tag='img')
			log.debug("adding %s to queue" % qitem)
			qitems.append(qitem)
		return qitems


# TODO: move save functionality into a base class
class ImageSaveRule(Rule):
	" Generic thread to save content "
	
	# TODO: move to config
	MIN_WIDTH = 250
	MIN_HEIGHT = 300
	imgParser = ImageFile.Parser()

	def process(self, resp_item):
		from_tag = resp_item.qitem.from_tag
		if from_tag == None or from_tag.lower() != 'img':
			log.info('Skipping, %s not from img tag (%s).' % (
					resp_item.response.geturl(), from_tag))
			return None
		try:
			self.imgParser.feed(resp_item.content)
			image = self.imgParser.close()
		except IOError, err:
			log.warn("IOError on image: %s:%s" % (resp_item.response.geturl(), err))
			return None
		
		size = image.size
		if size[0] < self.MIN_WIDTH or size[1] < self.MIN_HEIGHT:
			log.debug("image does not meet requirements %d,%d" % (size[0], size[1]))
			return None

		return self._save(image, resp_item.response.geturl(), resp_item.qitem.site_name)

	def save(self, content, url, name):
		" save the content "
		url_parts = urlparse.urlparse(url)
		full_name = "%s/%s/%s" % (self.config['save_dir'], name, os.path.basename(url_parts.path))
		# TODO: work with png and gifs
		if full_name[-4:] != '.jpg':
			full_name = "%s/%s.jpg" % (os.path.dirname(full_name), random.randint(100000,999999))
		try:
			fh = open(full_name, 'w')
			fh.write(content)
			fh.close()
		except IOError, err:
			log.warn("Failed saving '%s' from '%s:%s'" % (full_name, url, err))
