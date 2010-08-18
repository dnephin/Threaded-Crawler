"""
 A thread safe singleton agent for http fetching, and associated exceptions.
"""

import logging

import urllib2
from cookielib import CookieJar
import socket

from config import GlobalConfiguration


log = logging.getLogger("HTTPAgent")


class HttpResponse(object):
	"""
	A data transport object that holds the data returned from an HTTP Request.
	"""

	def __init__(self, code=0, message="", content=None):
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

	def success(self):
		"""
		@return: True if this object represents a successful http response, 
				False otherwise.
		@rtype : boolean
		"""
		return (code == 200)


class HttpAgent(object):
	"""
	A thread-safe singleton Http fetch object. This object should handle all
	exceptions and return a meaningful response to any clients.

	This object attempts to configure itself by getting a HttpAgentConfig object
	from the global config util. If none is found, it uses default values.

	This object accepts the following configuration values:
	http_timeout (Default 60): seconds to wait before timeing out the connection
	max_retry (Default 2): number of retry attempts to fetch the url if a timeout
			occurs.
	enable_cookies (Default: False): should this agent use a CookieJar and
			support cookies.
	"""

	__inst = None

	def __init__(self):
		"""
		Setup and configure the HttpAgent. This method will throw a ValueError 
		exception if the agent has already been instantiated.  You should be 
		using HttpAgent.getAgent() to get a reference to this object.
		"""
		if HttpAgent.__inst:
			raise ValueError("This singleton has already been created, Use getAgent()")
		HttpAgent.__inst = self
		self.configure()


	def configure(self):
		" Configure the HttpAgent from a HttpAgentConfig object or use defaults. "
		handlers = []
		config = GlobalConfiguration.get(self.__class__.__name__, {})
		self.http_timeout = config.get('http_timeout', 60)

		if config.get('enable_cookies', False):
			cookie_jar = CookieJar()
			handlers.append(urllib2.HTTPCookieProcessor(cookie_jar))

		self.max_retry = config.get('max_retry', 2)

		self.opener = urllib2.build_opener(*tuple(handlers))


	@staticmethod
	def getAgent():
		"""
		Return a reference to the singleton HttpAgent.

		@return a HttpAgent object
		"""
		if not HttpAgent.__inst:
			HttpAgent()
		return HttpAgent.__inst;


	def fetch(self, url):
		"""
		Fetch a url, and return the response object.

		@param url: the url to open
		@type  url: string
		@return: an HttpResponse object with the response code, message and content
		@rtype : HttpResponse
		"""
		http_response = HttpResponse()
		retry_count = 0

		while retry_count < self.max_retry:
			try:
				log.debug("Fetching %s [retry: %d]." % (url, retry_count))
				resp = self.opener.open(url, timeout=self.http_timeout)
				http_response.content = resp.read() 
				http_response.code = 200
				log.debug("Fetched  %s." % (resp.geturl()))
				break

			except socket.timeout, err:
				http_response.message = err
				log.warn("Socket timeout on %s [retry: %d]: %s" % (url, retry_count, err))
				retry_count += 1
				continue

			except urllib2.HTTPError, err:
				http_response.code = err.code
				http_response.message = err.message
				break

			except urllib2.URLError, err:
				http_response.message = err.reason
				log.warn("Unexpected Error %s: %s" % (url, err))
				break

		return http_response 
