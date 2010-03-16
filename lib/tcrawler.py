"""
 Threaded crawler.
 Prompts for a url, and uses threads to pull content from pages.
"""

import os
import logging
from Queue import Queue, Empty
from threads import ContentThread
from agent import HttpAgent
from dto import QueueItem
import time
from rules import HtmlPageImageLinksRule, ImageSaveRule


log = logging.getLogger("ThreadedCrawler")


class ParseConfiguration(object):
	" Responsible for parsing the configuration, and creating the rules objects "
	# recurse level, root save dir, default name parsing from url, retries, timeout
	pass


# TODO: remember command history in stdin mode, and serialize on exit, reserial on enter
# TODO: start_from_file_in mode
class Crawler(object):
	""" 
	The web crawler. Setup thread pool, and url queue.
	Get user input, and start processing.
	"""
	
	# TODO move to config
	num_threads = 100
	save_dir = "/home/daniel/media/del"

	def __init__(self):
		" Setup resources "
		# config
		self.config = {}
		# Queues of urls to process
		self.url_queue = Queue()
		# Url set to store already processed urls
		self.url_set = set()
		# processing threads
		self.thread_pool = []
		# http agent for fetching data
		agent = HttpAgent({}) # TODO: load config

		#TODO: move rules into config
		rules = [HtmlPageImageLinksRule({}), ImageSaveRule({'save_dir': self.save_dir})]
		for i in range(self.num_threads):
			self.thread_pool.append(ContentThread(self.url_queue, self.url_set, agent, rules))
			

	def start_from_stdin(self):
		" Read url from stdin, and fetch content "
		while True:
			input_cmd = raw_input("Enter command [SAVE,QUIT,WAIT_QUIT,INFO,HELP]: ")
			# look for commands
			if input_cmd == "QUIT":
				return self._shutdown()
			if input_cmd == "WAIT_QUIT":
				self._wait_on_queue()
				return self._shutdown()
			if input_cmd == "INFO":
				self._status()
				continue
			if input_cmd.startswith("SAVE"):
				self._save(input_cmd.lstrip("SAVE"))
				continue
			if input_cmd == 'CLEAR':
				self._clear_url_cache()
				continue
			print """
			SAVE url, name - save a url, using name for directory
			QUIT - quit immediately
			QUIT_WAIT - finish processing, quit gracefully
			CLEAR - clear the url cache, so we can repeat urls
			INFO - queue and thread status
			HELP - this message
			"""

	def _clear_url_cache(self):
		" Clear out the Url cache "
		# TODO
		pass


	def _save(self, input_line):
		" Start crawling from the input line "
		args = input_line.split(",", 2)
		if len(args) < 2:
			print "Missing input arguments."
			return

		# make the directory if non-existent
		dir_name = "%s/%s" % (self.save_dir, args[1])
		if not os.path.isdir(dir_name):
			try:
				os.mkdir(dir_name)
			except (IOError,OSError), err:
				log.warn("Error creating dir %s:%s" % (dir_name, err))
				return
		self.url_queue.put(QueueItem(args[0], site_name=args[1]))
	

	def _status(self,):
		" Print the status of the queue and threads. "
		print "Active Threads: %d" % sum(map(lambda t: t.isAlive(), self.thread_pool))
		print "Queue Size: %d" % self.url_queue.qsize()

	def _wait_on_queue(self):
		while (self.url_queue.qsize() and self.content_queue.qsize()):
			time.sleep(0.3)
		return

	def _shutdown(self):
		" end threads "
		# consume all remaining tasks
		try:
			while self.url_queue.get(False):
				self.url_queue.task_done()
		except Empty:
			pass
		# send the shutdown
		for thread in self.thread_pool:
			qi = QueueItem(None, shutdown=True)
			self.url_queue.put(qi)
		for thread in self.thread_pool:
			thread.join()


if __name__ == "__main__":
	import logging.config
	logging.config.fileConfig('./conf/logging.conf')
	crawler = Crawler()
	crawler.start_from_stdin()
