"""
 A thread safe singleton agent for http fetching, and associated exceptions.
"""

import logging

# urllib3
#from urllib3 import HTTPConnectionPool, MaxRetryError, TimeoutError

# urllib2
import urllib2
from cookielib import CookieJar
import socket
from config import GlobalConfiguration


log = logging.getLogger("HTTPAgent")


class HttpResponse(object):
	"""
	A data transport object that holds the return data from an HTTP Request.
	"""

	def __init__(self, code=0, message="", content=None):
		self.code = code
		self.message = message
		self.content = content

	def success(self):
		return (code == 200)


class HttpAgent(object):
	"""
	A thread-safe singleton Http fetch object. This object should handle all
	exceptions and return a meaningful response to any clients.

	This object attempts to configure itself by getting a HttpAgentConfig object
	from the global config util. If none is found, it uses default values.
	"""


	__inst = None

	def __init__(self):
		" Setup and configure the HttpAgent "
		if HttpAgent.__inst:
			raise ValueError("This singleton has already been created, Use getAgent()")
		HttpAgent.__inst = self
		self.configure()


	def configure(self):
		" Configure the HttpAgent from a HttpAgentConfig object or use defaults. "
		handlers = []
		config = GlobalConfiguration.get(self.__class__.__name__)
		self.http_timeout = config.get('http_timeout', 60)

		if config.get('enable_cookies', False):
			cookie_jar = CookieJar()
			handlers.append(urllib2.HTTPCookieProcessor(cookie_jar))

		self.opener = urllib2.build_opener(*tuple(handlers))


	@staticmethod
	def getAgent():
		if not HttpAgent.__inst:
			HttpAgent()
		return HttpAgent.__inst;

	def fetch(self, url):
		" fetch a url, and return the response object "
		# FIXME: BUG #100 retry on content read fail, and config for retry and timeout

		http_response = HttpResponse()
		
		try:
			log.debug("Fetching %s." % (url))
			resp = self.opener.open(url, timeout=self.http_timeout)
			http_response.content = resp.read() 
			http_response.code = 200
			log.debug("Fetched  %s." % (resp.geturl()))

		except socket.timeout, err:
			http_response.message = err
			log.warn("Socket timeout on %s: %s" % (url, err))
		except urllib2.HTTPError, err:
			http_response.code = err.code
			http_response.message = err.reason
		except urllib2.URLError, err:
			http_response.message = err.reason
			log.warn("Unexpected Erroron %s: %s" % (url, err))

		return http_response 
