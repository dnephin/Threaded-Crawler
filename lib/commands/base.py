"""
 Common Command objects used by the tcrawler, and base classes for more specific
 Command objects.

 These Commands are responsible for executing a task on a ProcessingThread
 given a WorkUnit object.
"""

import logging
import random
import ImageFile
import urlparse
import os
from BeautifulSoup import BeautifulSoup, SoupStrainer
from threads import WorkUnit

# agents
from httpagent import HttpAgent

log = logging.getLogger("Command")



class Command(object):
	"""
	The base class for all commands. All sub-classes must override execute().
	"""
	def __init__(self, chain):
		" configure the command. "
		self.chain = chain

	def execute(self, work_unit):
		" Execute the task given the work unit. "



class HttpFetchCommand(Command):
	" Base class for all commands that fetch something using the HttpAgent. "

	def fetch(self, url):
		http_agent = HtppAgent.getAgent()
		return http_agent.fetch(url)


class HttpFollowCommand(HttpFetchCommand):
	" Base class for all commands that parse an html page and follow a tag. "

	def parse_urls(self, soup_content, tag, url_property, base_url="", 
					pattern=None, captures=None):
		"""
		Parse the document and return a dictionary of urls that where contained in
		the url_property of the tag. These urls may be relative to the
		documents location. The value to each of the keys is another dictionary
		of meta data that was parsed from the url string.

		"""
		url_dict = {}
		# TODO: requires testing
		tags = soup_content.findAll(tag, attrs={url_property})
		for tag_item in tags:
			meta = {}
			matches = pattern.search(tag_item[url_property])
			if not matches:
				continue
			
			for i in range(matches.groups()):
				meta[captures[i]] = matches.group(i)
			
			abs_url = urlparse.urljoin(base_url, tag_item[url_property])
			url_dict[abs_url] = meta

		return url_dict


	def build_work_units(self, url_dict):
		" Build a list of WorkUnit objects from a url_dict object from parse_urls. "
		work_unit_list = []
		for command in self.chain:
			for url, meta_data in url_dict.iteritems():
				new_wu = WorkUnit(chain_commands=command.chain, url=url, 
						work_unit.meta_data.update(meta_data))
				work_unit_list.append(new_wu)

		return work_unit_list



class FollowA(HttpFollowCommand):
	"""
	Fetch a url (either as a parameter, or from the work_unit), and parse the
	document for <A href=""> that match regex. Any regex captures are stored
	in meta data with the labels procvided by captures parameter.  New
	WorkUnits are created for each of the urls, and returned.
	Returns None on error or when no tags match the regex.
	"""

	def __init__(self, url=None, regex=None, captures=None, chain=None):
		self.url = url
		self.regex = re.compile(regex)
		self.captures = captures
		Command.__init__(chain)


	def execute(self, work_unit):
		" Fetch the url, and add the content into the new work units. "
		if self.url:
			resp = self.fetch(self.url)
		elif work_unit.url:
			resp = self.fetch(work_unit.url)
		else:
			log.error("Could not fetch, no url to fetch.")
			return None

		if not resp.success:
			# TODO: better logging
			log.warn("Failed url: %s" % self.url)
			return None

		url_dict = self.parse_urls(
				BeautifulSoup(resp.content, parseOnlyThese=SoupStrainer('A')), 
				'A', 'href', 
				base_url=self.url,
				pattern=self.regex, 
				captures=self.captures)

		return self.build_work_units(url_dict)


class FollowAPartial(FollowA):
	"""
	Performs the same opperation as FollowA, but stops parsing the document
	once the stop_regex is reached.
	"""

	def __init__(self, url=None, regex=None, captures=None, chain=None, stop_regex=None):
		self.stop_regex = stop_regex
		FollowA.__init__(url=url, regex=regex, captures=captures, chain=chain)

	def parse_urls(self, soup_content, tag, url_property, base_url="", 
					pattern=None, captures=None):
		url_dict = {}
		# TODO: this needs to change so that it ends when stop_regex is hit
		tags = soup_content.findAll(tag, attrs={url_property})
		for tag_item in tags:
			meta = {}
			matches = pattern.search(tag_item[url_property])
			if not matches:
				continue
			
			for i in range(matches.groups()):
				meta[captures[i]] = matches.group(i)
			
			abs_url = urlparse.urljoin(base_url, tag_item[url_property])
			url_dict[abs_url] = meta

		return url_dict


class HtmlPageImageLinksRule(Rule):
	" Process an html page "

	def __init__(self, config):
		self.max_recurse = config.get('max_recurse', 1)

	def process(self, resp_item):
		from_tag = resp_item.qitem.from_tag
		if from_tag != None and from_tag.lower() != 'a':
			log.debug("Skipping, %s not from an anchor tag(<a>)" % resp_item)
			return None
		recurse = resp_item.qitem.recurse_level
		qitems = []
		content = BeautifulSoup(resp_item.content)
		if recurse < self.max_recurse:
			qitems += self.parse_pages(recurse+1, content, resp_item.qitem.url, 
					resp_item.qitem.site_name)

		qitems += self.parse_content(content, resp_item.qitem.url, resp_item.qitem.site_name)
		return qitems


	def parse_pages(self, recurse_level, content, url, name):
		" Parse the html page for more pages "
		qitems = []
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


	def parse_content(self, content, url, name):
		" Parse the html page for image content "
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

	def process(self, resp_item):
		from_tag = resp_item.qitem.from_tag
		if (from_tag == None or from_tag.lower() != 'img') and \
							resp_item.qitem.url[-4:] != '.jpg':
			log.info('Skipping, %s not from img tag (%s).' % (
					resp_item.qitem.url, from_tag))
			return None
		imgParser = ImageFile.Parser()
		try:
			imgParser.feed(resp_item.content)
			image = imgParser.close()
		except IOError, err:
			log.warn("IOError on image: %s:%s" % (resp_item.qitem.url, err))
			return None
		
		size = image.size
		if size[0] < self.MIN_WIDTH or size[1] < self.MIN_HEIGHT:
			log.info("Skipping, image does not meet requirements %d,%d" % (size[0], size[1]))
			return None

		return self._save(resp_item.content, resp_item.qitem.url, resp_item.qitem.site_name)

	def _save(self, content, url, name):
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
