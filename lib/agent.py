"""
 A thread safe singleton agent for http fetching, and associated exceptions.
"""

from socket import timeout
from ssl import SSLError
from dto import ResponseItem

import urllib2
import logging


log = logging.getLogger("ThreadedCrawler")

class UrlException(StandardError):
	" Thrown when an http request fails "
	def __init__(self, msg, requeue=True):
		BaseException.__init__(self, msg)
		self.requeue = requeue

	def __str__(self):
		return "UrlException[%s,requeue=%s]" % (self.message, self.requeue)


# TODO:  use one http agent (httpAgent class) and keep connection open using urllib3 (connection pool per domain) Must use redirect=False
class HttpAgent(object):
	" A singleton Http fetch object. Holds a connection pool for domains. "

	__inst = None

	def __init__(self, config):
		" Setup and configure the HttpAgent "
		if HttpAgent.__inst:
			raise ValueError("This singleton has already been created, Use getAgent()")
		HttpAgent.__inst = self
		self.http_timeout = config.get('http_timeout', 100)
		self.retry_errors = config.get('retry_rerrors', True)
		self.max_retry = config.get('max_retry', 3)

	@staticmethod
	def setup(config):
		if not HttpAgent.__inst:
			HttpAgent(config)

	@staticmethod
	def getAgent():
		if not HttpAgent.__inst:
			HttpAgent.setup({})
		return HttpAgent.__inst;

	def fetch(self, qitem):
		" fetch a page, and return the response url and content, or rise an  "
		try:
			resp = urllib2.urlopen(qitem.url, timeout=self.http_timeout)
			resp_item = ResponseItem(resp, qitem)
		except timeout, err:
			# just a timeout, we can retry
			qitem.retry_count += 1
			requeue = (qitem.retry_count <= self.max_retry)
			log.warn("Timeout on %d retry %s: %s" % (qitem.retry_count, qitem.url, err))
			raise UrlException("Timeout: %s" % err, requeue=requeue)

		except (urllib2.URLError, SSLError, ValueError), err:
			log.warn("Error on %s:%s" % (qitem.url, err))
			raise UrlException(str(err), requeue=self.retry_errors)
				
		return resp_item
