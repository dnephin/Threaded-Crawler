"""
 tcrawler is a highly configurable threaded web crawler.
"""

import logging
from Queue import Queue, Empty
from threading import Semaphore
import time

from crawler.threads import ProcessingThread, WorkUnit, QueueWatcher 
from crawler.config import GlobalConfiguration
from crawler.group import RoutingGroup
from common.stats import Statistics

log = logging.getLogger("ThreadedCrawler")


class Crawler(object):
	""" 
	The crawler loader. Responsible for reading the
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
		self.working_semaphore = QueueWatcher(self.config['number_threads'], 
				queue=self.work_queue)

		for i in range(self.config['number_threads']):
			self.thread_pool.append(
					ProcessingThread(self.work_queue, 
					self.working_semaphore))
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
			# TODO: add pause event, once implemented to stop processing.
			self._clear_queue()
		self._shutdown()
		self._print_stats()

	def _clear_queue(self):
		" Clear the queue of WorkUnits. "
		try:
			while self.work_queue.get(False):
				self.work_queue.task_done()
		except Empty:
			pass

	def _wait_on_work(self):
		"""
		Wait for all the processing threads to complete their tasks.
		"""
		time.sleep(1)
		while True:
			if self.working_semaphore.is_work_complete():
				log.warn("Shutting down...")
				return
			time.sleep(1)

	def _shutdown(self):
		"""
		Send a shutdown WorkUnit into the Queue for each thread. 
		"""
		for thread in self.thread_pool:
			self.work_queue.put(WorkUnit(shutdown=True))
		for thread in self.thread_pool:
			thread.join()

	def _print_stats(self):
		" Print statistics to stdout. "
		stats = Statistics.getObj().details()
		print '\n'.join(['%-35s %s' % (k, v) for (k, v) in stats.iteritems() ])


def load_config_module():
	"""
	Load the configuration module specified as a command line argument to this 
	script. 

	@return: a tuple of route, crawler_config, agent_config
	@rtype: tuple (of three dict)
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

	route = config_module.ROUTE or []

	if hasattr(config_module, 'ROUTING_DIR'):
		for group in RoutingGroup.load_from_dir(config_module.ROUTING_DIR):
			for command in group.route:
				route.append(command)

	return (route, config_module.CRAWLER_CONFIG, config_module.AGENT_CONFIG)


if __name__ == "__main__":
	import logging.config
	logging.config.fileConfig('./conf/logging.conf')
	crawler = Crawler(*load_config_module())
	crawler.start()
