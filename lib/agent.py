"""
 A thread safe singleton agent for http fetching, and associated exceptions.
"""

from dto import ResponseItem
import logging
from urlparse import urlparse

# urllib3
#from urllib3 import HTTPConnectionPool, MaxRetryError, TimeoutError

# urllib2
import urllib2
import socket



log = logging.getLogger("ThreadedCrawler")

class UrlException(Exception):
	" Thrown when an http request fails "
	def __init__(self, msg, requeue=True):
		Exception.__init__(self, msg)
		self.requeue = requeue
		self.message = msg

	def __str__(self):
		return "UrlException[%s,requeue=%s]" % (self.message, self.requeue)


class HttpAgent(object):
	" A singleton Http fetch object. Holds a connection pool for domains. "

	__inst = None

	def __init__(self, config):
		" Setup and configure the HttpAgent "
		if HttpAgent.__inst:
			raise ValueError("This singleton has already been created, Use getAgent()")
		HttpAgent.__inst = self
		self.http_timeout = config.get('http_timeout', 60)
		self.retry_errors = config.get('retry_rerrors', True)
		self.timeout_retry = config.get('timeout_retry', 2)
		self.max_retry = config.get('max_retry', 3)
		self.num_conns = config.get('num_conns', 100)
		# start the collection pool as a dictionary
		self.conn_pools = {}

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
		" fetch a page, and return the response url and content, or raise an exception "
		# get the correct pool

		try:
			resp = urllib2.urlopen(qitem.url, timeout=self.http_timeout)
			resp_item = ResponseItem(resp, qitem)
		except (socket.timeout, urllib2.URLError), err:
			qitem.retry_count += 1
			requeue = (qitem.retry_count <= self.timeout_retry)
			log.warn("Timeout on %d retry %s: %s" % (qitem.retry_count, qitem.url, err))
			raise UrlException("Timeout: %s" % err, requeue=requeue)

		return resp_item
