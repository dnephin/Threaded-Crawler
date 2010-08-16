"""
 Threads for tcrawler.
"""

import threading
import logging


log = logging.getLogger("ProcessingThread")

class WorkUnit(object):
	"""
	This class represents a single unit of work that will be run on a
	WorkerThread.  These units will be passed to the execute() method
	of the Command object. Usually represents a url to fetch, or an
	item to store locally.
	"""

	def __init__(self, chain_commands=None, url=None, meta_data=None):
		"""
		Initialize a new WorkUnit object. 
		Parameters:
			chain_commands - a list containing Command objects
			url - the to fetch to carry out this unit of work
			meta_data - data that has been build up by previous commands
						that executes previously in the chain
		"""
		self.chain_commands = chain_commands
		self.url = url
		self.meta_data = meta_data
		self.shutdown = False

	def isShutdown(self):
		" Returns true when this WorkUnit represents a shutdown request. "
		return self.shutdown



class ProcessingThread(threading.Thread):
	"""
	This thread consumes WorkUnit objects from the queue.  It calls
	execute() on each Command object contained in the chain of the
	WorkUnit object.  It then retrieves any newly created WorkUnit
	objects from the Command and adds them back into the queue.
	"""

	def __init__(self, work_queue):
		"""
		Initialize the thread, and start it. 
		Parameters:
			work_queue - a thread safe queue of WorkUnit objects
		"""
		self.work_queue = work_queue
		threading.Thread.__init__(self)
		self.start()

	def run(self):
		" Run the thread, comsume from queue, execute Command, add to queue.  "
		while True:
			work_unit = self.work_queue.get()
			if work_unit.isShutdown():
				log.info("Received shutdown request.")
				return
			log.info("Processing: %s" % (work_unit))
			
			# execute commands 
			new_work_units = []
			for command in work_unit.chain_commands:
				try:
					new_work_units.extend(command.execute(work_unit))
				except Exception, err:
					log.warn("Unexpected Exception from Command: %s " % err)
					continue

			self.work_queue.task_done()
