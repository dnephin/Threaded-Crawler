"""
 Threads for tcrawler.
"""

import threading
import logging
from agent import UrlException


log = logging.getLogger("ThreadedCrawler")

class ContentThread(threading.Thread):
	"""
	These threads consume qitems from the queue, use the HttpAgent to fetch the
	content of that url, then send it through the rules for processing. Finally
	adding any produced QueueItems back into the Queue.
	"""
	def __init__(self, url_queue, url_set, agent, rules):
		" Setup thread, and save references to queue, url set, agent and rules "
		self.url_set = url_set
		self.url_queue = url_queue
		self.agent = agent
		self.rule_list = rules
		threading.Thread.__init__(self)
		self.start()

	def run(self):
		" run the thread, comsume from queue, fetch url, add to queue  "
		while True:
			qitem = self.url_queue.get()
			if qitem.shutdown:
				return
			log.info("Processing: %s" % (qitem))
			
			# fetch url
			try:
				resp_item = self.agent.fetch(qitem)
			except UrlException, err:
				if err.requeue:
					self.url_queue.put(qitem)
				log.warn(err)
				self.url_queue.task_done()
				continue

			qitem_list = []
			for rule in self.rule_list:
				qitems = rule.process(resp_item)
				if qitems:
					qitem_list += qitems

			for qitem in qitem_list:
				self.url_queue.put(qitem)
			# clear task
			self.url_queue.task_done()

