"""
 tcrawler is a highly configurable threaded web crawler.
"""

import logging
from Queue import Queue, Empty
import time

from threads import ProcessingThread, WorkUnit 
from config import GlobalConfiguration

log = logging.getLogger("ThreadedCrawler")


class Crawler(object):
	""" 
	The main control class for the crawler. Responsible for reading the
	configuration, storing agent configuration in the GlobalConfiguration,
	starting thread pool and sending the first Command into the Queue.
	"""

	DEFAULT_NUMBER_THREADS = 100
	
	def __init__(self, config_module):
		" Setup resources "

		self.load_config(config_module)

		# Queue of work units
		self.work_queue = Queue()
		# processing threads
		self.thread_pool = []

		for i in range(self.config['number_threads']):
			self.thread_pool.append(ProcessingThread(self.work_queue))
		log.info("Started %d threads." % self.config['number_threads'])

	def load_config(self, config_module):
		" Read the config module, and load settings into GlobalConfiguration. "

		# crawler config
		self.config = {}
		if hasattr(config_module, 'CRAWLER_CONFIG'):
			self.config['number_threads'] = config_module.CRAWLER_CONFIG.get(
					'number_threads', self.DEFAULT_NUMBER_THREADS)
		else:
			self.config['number_threads'] = self.DEFAULT_NUMBER_THREADS

		# Agents config
		if hasattr(config_module, 'AGENT_CONFIG'):
			GlobalConfiguration.config.update(config_module.AGENT_CONFIG)

		# Route
		self.route = config_module.ROUTE

			

	def start(self):
		" Build the first Work Unit and send it to the Queue. "
		for command in self.route:
			work_unit = WorkUnit(command)
			self.work_queue.put(work_unit)

		try:
			self._wait_on_queue()
		except KeyboardInterrupt, err:
			log.warn("Caught KeyboardInteruupt, shutting down.")
			self._clear_queue()
		self._shutdown()


	def _clear_queue(self):
		" Clear the queue of WorkUnits. "
		try:
			while self.work_queue.get(False):
				self.work_queue.task_done()
		except Empty:
			pass

	# TODO: fix so that it can be killed
	def _wait_on_queue(self):
		time.sleep(3)
		self.work_queue.join()
		return

	def _shutdown(self):
		" end threads "
		# send the shutdown
		for thread in self.thread_pool:
			self.work_queue.put(WorkUnit(shutdown=True))
		for thread in self.thread_pool:
			thread.join()



def load_config_module():
	import sys
	if len(sys.argv) < 2:
		print "No config module specified."
		sys.exit(-1)
	return __import__(sys.argv[1])


if __name__ == "__main__":
	import logging.config
	logging.config.fileConfig('./conf/logging.conf')
	crawler = Crawler(load_config_module())
	crawler.start()
