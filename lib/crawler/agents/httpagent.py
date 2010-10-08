"""
 A thread safe singleton agent for http fetching, and associated exceptions.
"""

import logging

import urllib2
from cookielib import CookieJar, MozillaCookieJar
import socket
from threading import Lock
import re

from common.pattern import Singleton
from crawler.config import GlobalConfiguration


log = logging.getLogger("HTTPAgent")


class HttpResponse(object):
	"""
	A data transport object that holds the data returned from an HTTP Request.
	"""

	def __init__(self, code=0, message="", content=None, url=None):
		"""
		Instantiate a new HttpResponse object.

		@param code: the http response code
		@type  code: integer
		@param message: the http response line, or an exception message
		@type  message: string
		@param content: the contents of the page
		@type  content: string of bytes, or None
		"""
		self.code = code
		self.message = message
		self.content = content
		self.url = url

	def success(self):
		"""
		@return: True if this object represents a successful http response, 
				False otherwise.
		@rtype:boolean
		"""
		return (self.code == 200)


class HttpAgent(object):
	"""
	A thread-safe singleton Http fetch object. This object should handle all
	exceptions and return a meaningful response to any clients.

	This object attempts to configure itself by getting a HttpAgentConfig object
	from the global config util. If none is found, it uses default values.

	This object accepts the following configuration values:
		- http_timeout (Default 60) 
			- seconds to wait before timeing out the connection
		- max_retry (Default 2) 
			- number of retry attempts to fetch the url if a timeout occurs.
		- enable_cookies (Default: False) 
			- should this agent use a CookieJar and support cookies.
		- cookie_file (Default: /tmp/crawler_cookies):
			- the filename used to persist cookies
		- user_agent (Default: Mozilla/5.0):
			- the string to use as the user agent header in Http Requests
	"""
	__metaclass__ = Singleton
	
	ENCODING_REGEX = re.compile('.*charset=(.*);?', re.IGNORECASE)
	" @cvar: a compiled regex for finding the content encoding in the headers. "

	def __init__(self):
		"""
		Setup and configure the HttpAgent. This method will throw a ValueError 
		exception if the agent has already been instantiated.  You should be 
		using HttpAgent.getAgent() to get a reference to this object.
		"""
		self.configure()


	def configure(self):
		" Configure the HttpAgent from a HttpAgentConfig object or use defaults. "
		handlers = []
		config = GlobalConfiguration.get(self.__class__, {})
		self.http_timeout = config.get('http_timeout', 60)

		if config.get('enable_cookies', False):
			cookie_jar = MozillaCookieJar(config.get('cookie_file', '/tmp/crawler_cookies'))
			handlers.append(urllib2.HTTPCookieProcessor(cookie_jar))

		self.max_retry = config.get('max_retry', 3)

		self.opener = urllib2.build_opener(*tuple(handlers))
		self.opener.addheaders = [('User-agent', 
				config.get('user_agent', 'Mozilla/5.0'))]


	@staticmethod
	def getAgent():
		"""
		Return a reference to the singleton HttpAgent.
		@return: a HttpAgent object
		"""
		return HttpAgent()


	def fetch(self, url):
		"""
		Fetch a url, and return the response object.

		@param url: the url to open
		@type  url: string
		@return: an HttpResponse object with the response code, message and content
		@rtype: HttpResponse
		"""
		http_response = HttpResponse()
		retry_count = 0

		while retry_count < self.max_retry:
			try:
				log.debug("Fetching %s [retry: %d]." % (url, retry_count))
				resp = self.opener.open(url, timeout=self.http_timeout)
				http_response.code = 200
				http_response.url = resp.geturl()
				http_response.content = self._decode_content(resp)
				log.debug("Fetched  %s." % (resp.geturl()))
				break

			except urllib2.HTTPError, err:
				http_response.code = err.code
				http_response.message = err.strerror
				break

			except (socket.timeout, urllib2.URLError), err:
				if type(err) == urllib2.URLError and not type(err.reason) == socket.timeout:
					if hasattr(err.reason, 'strerror'):
						reason = err.reason.strerror
					else:
						rason = err.reason
					http_response.message = reason
					log.warn("Unexpected Error %s: %s" % (url, reason))
					break
					
				http_response.message = err
				log.warn("Socket timeout on %s [retry: %d]: %s" % (url, retry_count, err))
				retry_count += 1

		return http_response


	def _decode_content(self, resp):
		"""
		Attempt to find the content type header, and decode the content using that 
		type.

		@param resp: the http response object
		@type  resp: 
		@return: the content of the response object as unicode string, or the raw data
		@rtype: unicode or str
		"""
		header = resp.info().typeheader
		if not header:
			return resp.read()

		matches = self.ENCODING_REGEX.search(header)
		if not matches:
			return resp.read()

		return resp.read().decode(matches.group(1))
		
