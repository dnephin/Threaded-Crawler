"""
 tcrawler is a highly configurable threaded web crawler.
"""

import logging
from Queue import Queue, Empty
from threading import Semaphore
import time

from threads import ProcessingThread, WorkUnit 
from config import GlobalConfiguration

log = logging.getLogger("ThreadedCrawler")


class CrawlerLoader(object):
	""" 
	The tcrawler Loader. Responsible for reading the
	configuration, storing agent configuration in the GlobalConfiguration,
	starting thread pool and sending the first Command into the Queue.
	"""

	DEFAULT_NUMBER_THREADS = 100
	
	def __init__(self, route, crawler_config, agent_config):
		"""
		Create a new instance of Crawler object. Creates the work queue
		and thread pool.

		@param route: the list of command objects that define the route
					the crawler will traverse
		@type  route: list of L{commands.base.Command} objects
		@param crawler_config: configuration of the crawler
		@type  crawler_config: dictionary
		@param agent_config: configuration map for any agents the crawler will use
		@type  agent_config: dictionary
		"""
		self.config = {}
		self.config['number_threads'] = crawler_config.get(
					'number_threads', self.DEFAULT_NUMBER_THREADS)

		GlobalConfiguration.config.update(agent_config)
		self.route = route 

		# Queue of work units
		self.work_queue = Queue()
		# processing threads
		self.thread_pool = []
		self.working_semaphore = Semaphore(self.config['number_threads'])

		for i in range(self.config['number_threads']):
			self.thread_pool.append(ProcessingThread(self.work_queue, self.working_semaphore))
		log.info("Started %d threads." % self.config['number_threads'])


	def start(self):
		" Build the first Work Unit and send it to the Queue. "
		for command in self.route:
			work_unit = WorkUnit(command)
			self.work_queue.put(work_unit)

		try:
			self._wait_on_work()
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
	def _wait_on_work(self):
		"""
		Wait for all the processing threads to complete their tasks.
		"""
		time.sleep(1)
		work_done_count = 0
		work_done_max = 4
		while work_done_count < work_done_max:
			# FIXME: this breaks if a thread crashes
			# TODO: superclass semaphore to make _Semaphore__Value atomic ?
			if (self.work_queue.empty() and 
					self.working_semaphore._Semaphore__value == self.config['number_threads']):
				work_done_count += 1
				log.warn("Shutting down in %d..." % (work_done_max - work_done_count))
			time.sleep(1)
		return

	def _shutdown(self):
		"""
		Send a shutdown WorkUnit into the Queue for each thread. 
		"""
		for thread in self.thread_pool:
			self.work_queue.put(WorkUnit(shutdown=True))
		for thread in self.thread_pool:
			thread.join()



def load_config_module():
	"""
	Load the configuration module specified as a command line argument to this 
	script. 

	@return: a tuple of route, crawler_config, agent_config
	@rtype : tuple (of three dict)
	"""
	import sys
	if len(sys.argv) < 2:
		print "No config module specified."
		sys.exit(-1)
	config_module = __import__(sys.argv[1])

	if not hasattr(config_module, 'AGENT_CONFIG'):
		sys.stderr('Config module requires an "AGENT_CONFIG" dictionary')
		sys.exit(-1)
	if not hasattr(config_module, 'CRAWLER_CONFIG'):
		sys.stderr('Config module requires an "CRAWLER_CONFIG" dictionary')
		sys.exit(-1)
	if not hasattr(config_module, 'ROUTE'):
		sys.stderr('Config module requires an "ROUTE" dictionary')
		sys.exit(-1)

	return (config_module.ROUTE, config_module.CRAWLER_CONFIG, 
			config_module.AGENT_CONFIG)


if __name__ == "__main__":
	import logging.config
	logging.config.fileConfig('./conf/logging.conf')
	crawler = CrawlerLoader(*load_config_module())
	crawler.start()
