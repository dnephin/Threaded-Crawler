"""
 Common Command objects used by the tcrawler, and base classes for more specific
 Command objects.

 These Commands are responsible for executing a task on a ProcessingThread
 given a WorkUnit object.
"""

import logging
import urlparse
import re
from BeautifulSoup import BeautifulSoup, SoupStrainer
from threads import WorkUnit

# agents
from agents.httpagent import HttpAgent

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

	def __repr__(self):
		return "<%s>" % self.__class__.__name__



class HttpFetchCommand(Command):
	" Base class for all commands that fetch something using the HttpAgent. "

	def __init__(self, url=None):
		self.url = url
		Command.__init__(self, chain=None)

	def execute(self, work_unit):
		self.fetch(self.url)
		return None

	def fetch(self, url):
		http_agent = HttpAgent.getAgent()
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
		log.debug("Parsing %s for %s.%s tags." % (base_url, self._sre(tag), url_property))
		url_dict = {}
		# TODO: requires testing
		tags = soup_content.findAll(tag, attrs={url_property: True} )
		log.debug("Found %d tags." % len(tags))
		for tag_item in tags:
			meta = {}
			matches = pattern.search(tag_item[url_property])
			if not matches:
				continue
	
			for i in range(len(matches.groups()) - 1):
				meta[captures[i]] = matches.group(i + 1)
			
			abs_url = urlparse.urljoin(base_url, tag_item[url_property])
			url_dict[abs_url] = meta

		return url_dict


	def build_work_units(self, url_dict, work_unit):
		" Build a list of WorkUnit objects from a url_dict object from parse_urls. "
		work_unit_list = []
		log.debug("Building %d new work units." % (len(self.chain) * len(url_dict)))
		for command in self.chain:
			for url, meta_data in url_dict.iteritems():
				if work_unit.meta_data:
					combined_meta_data = work_unit.meta_data.copy()
					combined_meta_data.update(meta_data)
				else:
					combined_meta_data = meta_data

				new_wu = WorkUnit(command=command, url=url, 
						meta_data=combined_meta_data)
				work_unit_list.append(new_wu)

		return work_unit_list

	@staticmethod
	def _sre(s):
		" Output as a readable string, either a regex, or the plain string. "
		if hasattr(s, 'pattern'):
			return s.pattern
		return s


class FollowA(HttpFollowCommand):
	"""
	Fetch a url (either as a parameter, or from the work_unit), and parse the
	document for <A href=""> that match regex. Any regex captures are stored
	in meta data with the labels procvided by captures parameter.  New
	WorkUnits are created for each of the urls, and returned.
	Returns None on error or when no tags match the regex.
	"""

	TAG_REGEX = re.compile('^[aA]$')
	URL_PROPERTY = 'href'

	def __init__(self, url=None, regex=None, captures=None, chain=None):
		self.url = url
		self.regex = re.compile(regex)
		self.captures = captures
		Command.__init__(self, chain)


	def execute(self, work_unit):
		" Fetch the url, and add the content into the new work units. "
		if self.url:
			resp = self.fetch(self.url)
		elif work_unit.url:
			resp = self.fetch(work_unit.url)
			self.url = work_unit.url
		else:
			log.error("Could not fetch, no url to fetch.")
			return None

		if not resp.success:
			# TODO: better logging
			log.warn("Failed url: %s" % self.url)
			return None

		url_dict = self.parse_urls(
				self.get_soup_content(resp.content),
				self.TAG_REGEX, self.URL_PROPERTY,
				base_url=self.url,
				pattern=self.regex, 
				captures=self.captures)

		return self.build_work_units(url_dict, work_unit)

	def get_soup_content(self, content):
		return BeautifulSoup(content, parseOnlyThese=SoupStrainer(self.TAG_REGEX)) 

	def __repr__(self):
		return "<%s regex=%s>" % (self.__class__.__name__, self.regex.pattern)

class FollowAPartial(FollowA):
	"""
	Performs the same opperation as FollowA, but stops parsing the document
	once the stop_regex is reached.
	"""

	def __init__(self, url=None, regex=None, captures=None, chain=None, stop_regex=None):
		self.stop_regex = re.compile(stop_regex)
		FollowA.__init__(self, url=url, regex=regex, captures=captures, chain=chain)

	def get_soup_content(self, content):
		matches = self.stop_regex.search(content)
		if not matches:
			log.warn("Stop regex (%s) was not found in the document %s" % (self.regex.pattern, self.url))
		else:
			content = content[:matches.start()]
		return super(FollowAPartial, self).get_soup_content(content)


class FollowIMG(FollowA):
	"""
	Fetch a url (either as a parameter, or from the work_unit), and parse the
	document for <IMG src=""> that match regex. Any regex captures are stored
	in meta data with the labels provided by captures parameter.  New
	WorkUnits are created for each of the urls, and returned.
	Returns None on error or when no tags match the regex.
	"""

	TAG_REGEX = re.compile('^(?:IMG|img|Img)$')
	URL_PROPERTY = 'src'
