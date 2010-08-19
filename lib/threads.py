"""
 Threads for tcrawler.
"""

import threading
import logging
import traceback


log = logging.getLogger("ProcessingThread")

class WorkUnit(object):
	"""
	A data transport object that represents a single unit of work that 
	will be run on a ProcesingThread.  These units will be passed to the 
	execute() method of the Command object stored in this unit. Usually 
	represents a url to fetch, or an item to store locally.
	"""

	def __init__(self, command=None, url=None, meta_data=None, shutdown=False):
		"""
		Instantiate a new WorkUnit object.

		@param command: a Command objects that performs an operation
		@type  command: Command
		@param url: the url to fetch to carry out this unit of work
		@type  url: string
		@param meta_data: data that has been built up by commands
				that were executed above this unit in the chain
		@type  meta_data: dict
		"""
		self.command = command
		self.url = url
		self.meta_data = meta_data
		self.shutdown = shutdown

	def isShutdown(self):
		"""
		@return: true when this WorkUnit represents a shutdown request, 
				false otherwise
		"""
		return self.shutdown

	def __repr__(self):
		if self.isShutdown():
			return "WorkUnit - Shutdown"
		return "WorkUnit - %s, url[%s]" % (self.command, self.url)



class ProcessingThread(threading.Thread):
	"""
	This thread consumes WorkUnit objects from the queue.  It calls
	execute() on the Command object in the WorkUnit.  It then retrieves any 
	newly created WorkUnit objects from the Command and adds them back into 
	the queue.

	"""
	# TODO: doc semaphore param
	def __init__(self, work_queue, work_semaphore):
		"""
		Initialize the thread, and start it.

		@param work_queue: a thread safe queue of WorkUnit objects
		@type  work_queue: Queue
		"""
		self.work_queue = work_queue
		self.work_semaphore = work_semaphore
		threading.Thread.__init__(self)
		self.start()


	def run(self):
		"""
		Run the thread, comsume from queue, execute Command, add to queue.
		Continue until it receives a shutdown WorkUnit.
		"""
		while True:
			work_unit = self.work_queue.get()
			self.start_working()
			if work_unit.isShutdown():
				log.debug("Received shutdown request.")
				self.stop_working()
				return
			log.info("Processing: %s" % (work_unit))
			
			try:
				new_work_units = work_unit.command.execute(work_unit)
			except Exception, err:
				log.warn("Unexpected Exception from Command: %s\n%s " % (err, traceback.format_exc()))
				self.stop_working()
				continue

			if new_work_units:
				for new_work_unit in new_work_units:
					self.work_queue.put(new_work_unit)
			self.stop_working()


	def stop_working(self):
		"""
		Notify the queue that the work is complete on the last unit that was
		pulled, and set the working status flag to False.
		"""
		self.work_queue.task_done()
		self.work_semaphore.release()


	def start_working(self):
		"""
		Increment the working counter.
		"""
		self.work_semaphore.acquire()

