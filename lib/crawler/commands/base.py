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
from crawler.threads import WorkUnit

# agents
from crawler.agents.httpagent import HttpAgent
from common.stats import Statistics

log = logging.getLogger("Command")



class Command(object):
	"""
	The base class for all commands. All sub-classes must override execute().

	Command objects should always remain immutable, since they are passed around
	to many WorkUnit objects, on many threads.  If their state change the 
	behaviour is undefined.
	"""
	def __init__(self, chain):
		" configure the command. "
		self.chain = chain

	def execute(self, work_unit):
		"""
		Execute the task given the work unit. 
		@param work_unit: the details of the work to perform
		@type  work_unit: L{crawler.threads.WorkUnit}
		"""

	def __repr__(self):
		return "%s(chain=%r)" % (self.__class__.__name__, self.chain)


	def get_command_chain(self):
		"""
		Return the chain of Commands assigned to this Command. 
		
		@return: the list of Command objects
		@rtype: list
		"""
		return self.chain



class HttpFetchCommand(Command):
	" Base class for all commands that fetch something using the HttpAgent. "

	def __init__(self, url=None):
		self.url = url
		Command.__init__(self, chain=None)

	def execute(self, work_unit):
		self.fetch(self.url)
		return None

	def fetch(self, url):
		"""
		Fetch a url by performing a GET request using the HttpAgent.

		@param url: the url to fetch
		@type  url: string
		@return: a response object on success, or None of failure
		@rtype: HttpResponse
		"""
		http_agent = HttpAgent.getAgent()
		resp = http_agent.fetch(url)
		if not resp.success():
			log.warn("Failed url: %s" % url)
			Statistics.getObj().stat('http_fail_%d' % resp.code)
			return None

		Statistics.getObj().stat('http_success')
		return resp 


class HttpFollowCommand(HttpFetchCommand):
	" Base class for all commands that parse an html page and follow a tag. "

	def __init__(self, url=None, regex=None, text_regex=None,
			captures=None, chain=None):
		"""
		@param url: the url to fetch
		@type  url: string
		@param regex: the regex of the urls to follow
		@type  regex: string or compiled regex
		@param text_regex: the regex to match to the body of the tag
		@type  text_regex: string or compiled regex
		@param captures: the name given to captures done by regex
		@type  captures: list of strings
		"""
		self.url = url
		self.regex = re.compile(regex)
		self.captures = captures
		self.text_regex = None
		if text_regex:
			self.text_regex = re.compile(text_regex)
		Command.__init__(self, chain)


	def execute(self, work_unit):
		"""
		Fetch the url stored in work_unit.  If that is null, fetch the url 
		assgined to this command object. Parse the document for urls to 
		follow and then build new work units for these urls.

		@return: the new list of work units that were generated by this command
				or None
		@rtype:  list
		"""
		if self.url:
			work_unit.url = self.url
		
		if not work_unit.url:
			log.error("Could not fetch, the WorkUnit does not contain a url.")
			return None

		resp = self.fetch(work_unit.url)
		if not resp:
			return None

		url_dict = self.parse_urls(
				self.get_soup_content(resp.content),
				self.TAG_REGEX, self.URL_PROPERTY,
				base_url=resp.url,
				pattern=self.regex, 
				captures=self.captures)

		return self.build_work_units(url_dict, work_unit)

	def get_soup_content(self, content):
		return BeautifulSoup(content, parseOnlyThese=SoupStrainer(self.TAG_REGEX)) 

	def __repr__(self):
		return "%s(url=%r, regex=%r, captures=%r, chain=%r)" % (self.__class__.__name__, 
				self.url, self.regex.pattern, self.captures, self.chain)

	def parse_urls(self, soup_content, tag, url_property, base_url="", 
					pattern=None, captures=None):
		"""
		Parse the document and return a dictionary of urls that where contained in
		the url_property of the tag. These urls may be relative to the
		documents location. The value to each of the keys is another dictionary
		of meta data that was parsed from the url string.

		@param soup_content: a BeautifulSoup object of the fetched page
		@type  soup_content: BeautifulSoup
		@param tag: the html tag to follow
		@type  tag: regex or string
		@param url_property: the attribute name that contains the url in the 
				tag to follow
		@type  url_property: string or regex
		@param base_url: the url of the current page used to create an absolute
				url from a relative one
		@type  base_url: string
		@param pattern: the url regex to follow
		@type  pattern: regex
		@param captures: the names of the captured params from pattern
		@type  captures: list of strings
		@return: a dictionary with keys of urls, to a dict of meta data
		@rtype: dict
		"""
		log.debug("Parsing %s for %s.%s tags." % (base_url, self._sre(tag), url_property))
		url_dict = {}

		tags = soup_content.findAll(tag, attrs={url_property: True} )
		log.debug("Found %d tags." % len(tags))

		for tag_item in tags:
			if self.text_regex and not self.text_regex.search(tag_item.text):
				log.debug("Skipping tag '%s' because text_regex did not match." % (
						tag_item))
				continue
			meta = {}
			matches = pattern.search(tag_item[url_property])
			if not matches:
				continue

			for i in range(len(matches.groups())):
				meta[captures[i]] = matches.group(i + 1)
			
			abs_url = urlparse.urljoin(base_url, tag_item[url_property])
			log.debug("Built %s from [%s][%s]" % (abs_url, base_url, tag_item[url_property]))
			url_dict[abs_url] = meta

		return url_dict


	def build_work_units(self, url_dict, work_unit):
		""" 
		Build a list of WorkUnit objects from a url_dict object from parse_urls. 

		@param url_dict: map of urls to meta data captured from the regex
		@type  url_dict: dictionary
		@param work_unit: a L{threads.WorkUnit} object that was given to this
				command to perform tasks with
		@type  work_unit: L{threads.WorkUnit}
		"""
		work_unit_list = []
		log.debug("Building %d new work units." % (len(self.chain) * len(url_dict)))
		for command in self.get_command_chain():
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
			log.warn("Stop regex (%s) was not found in the document." % (self.regex.pattern))
		else:
			content = content[:matches.start()]
			
		return super(FollowAPartial, self).get_soup_content(content)


class RecursiveFollowA(FollowAPartial):
	"""
	Follow the <A href=""> links that match the regex until some condition 
	is met.  This condition is a regex pattern that will appear on the page.
	This Command adds itself to its own chain of commands.
	"""

	def get_command_chain(self):
		return self.chain + [self]


class FollowIMG(HttpFollowCommand):
	"""
	Fetch a url (either as a parameter, or from the work_unit), and parse the
	document for <IMG src=""> that match regex. Any regex captures are stored
	in meta data with the labels provided by captures parameter.  New
	WorkUnits are created for each of the urls, and returned.
	Returns None on error or when no tags match the regex.
	"""

	TAG_REGEX = re.compile('^(?:IMG|img|Img)$')
	URL_PROPERTY = 'src'



class StoreCommand(HttpFetchCommand):
	"""
	Base class for all commands that store a page.
	"""

	def execute(self, work_unit):
		resp = self.fetch(work_unit.url)
		if not resp:
			return None

		if self.content_passes_conditions(resp.url, resp.content):
			self.store(resp.url, resp.content, work_unit)

		return None


	def content_passes_conditions(self, url, content):
		"""
		Check if the response meets the conditions that are required to save
		this content.

		@param url: the url of this content
		@type  url: string
		@param content: the content of the response
		@type  content: string
		@return: True if the content should be stored, False otherwise
		@rtype: boolean
		"""
		return True


	def store(self, url, content, work_unit):
		"""
		Store the content.
		@param url: the url of this content
		@type  url: string
		@param content: the content of the response
		@type  content: string
		@param work_unit: the work_unit that was sent to this Command for processing
		@type  work_unit: L{WorkUnit}
		"""
		


