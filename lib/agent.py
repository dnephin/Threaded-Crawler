"""
 A thread safe singleton agent for http fetching, and associated exceptions.
"""

from dto import ResponseItem
import logging
from urllib3 import HTTPConnectionPool, MaxRetryError, TimeoutError
from urlparse import urlparse


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
		url_parts = urlparse(qitem.url)
		host = url_parts.hostname
		port = url_parts.port or None
		# TODO: synchronize this
		if host not in self.conn_pools:
			self.conn_pools[host] = HTTPConnectionPool(host, port=port, timeout=self.http_timeout,
					maxsize=self.num_conns)
		pool = self.conn_pools[host]

		try:
			resp = pool.get_url(qitem.url, retries=self.max_retry, redirect=False)
			resp_item = ResponseItem(resp, qitem)
		except TimeoutError, err:
			qitem.retry_count += 1
			requeue = (qitem.retry_count <= self.timeout_retry)
			log.warn("Timeout on %d retry %s: %s" % (qitem.retry_count, qitem.url, err))
			raise UrlException("Timeout: %s" % err, requeue=requeue)
		except MaxRetryError, err:
			raise UrlException("MaxRetry for %s: %s" % (qitem.url, err))

		# handle redirects
		if resp.status in [301, 302, 303, 307] and 'location' in resp.headers:
			log.info("Redirecting[%d] %s => %s" % (resp.status, qitem.url, resp.headers.get('location')))
			qitem.url = resp.headers.get('location')
			return self.fetch(qitem)

		return resp_item
