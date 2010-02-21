"""
 Data transport objects for sending requests and their content 
 around in the crawler.
"""

class QueueItem(object):
	" A structure to store requests in the queue "
	def __init__(self, url, recurse_level=0, site_name=None, retry_count=0, 
			from_tag=None, shutdown=False):
		self.url = None
		if url:
			self.url = url.strip()
		self.recurse_level = recurse_level
		self.site_name = site_name
		self.retry_count = retry_count
		self.from_tag = from_tag
		self.shutdown = shutdown

	def __repr__(self):
		return "QueueItem<%s,recurse:%d,retries:%s>" % (self.url, 
				self.recurse_level, self.retry_count)

class ResponseItem(object):
	" A structure to store responses from the HttpAgent "
	def __init__(self, response, qitem):
		self.response = response
		self.content = response.data
		self.qitem = qitem

	def __repr__(self):
		return "ResponseItem<%s,size:%d,from:%s>" % (self.qitem.url,
				len(self.content), self.qitem.from_tag)
