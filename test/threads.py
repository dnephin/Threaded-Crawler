"""
Unit tests for threads class of the tcrawler.
"""

import unittest
from Queue import Queue
from threading import Semaphore
import time

from crawler.threads import ProcessingThread, WorkUnit
from test import SimpleCommand, ManyCommand, ExceptionCommand, CounterObject



class TestProcessingThread(unittest.TestCase):

	def setUp(self):
		self.q = Queue()
		self.s = Semaphore(5)
		self.t = ProcessingThread(self.q, self.s)

	def tearDown(self):
		self.q.put(WorkUnit(shutdown=True))
		self.t.join()


	def test_start_stop_working(self):
		"""
		Test that start_working and stop_working properly alter the semaphore.
		"""
		self.t.start_working()
		self.assertEquals(self.s._Semaphore__value, 4)
		w = WorkUnit(SimpleCommand())
		self.q.put(w)
		self.q.get()
		self.t.stop_working()
		self.assertEquals(self.s._Semaphore__value, 5)


	def test_run(self):
		" Test that the thread runs the execute of command. "
		w = WorkUnit(SimpleCommand())
		self.q.put(w)
		time.sleep(0.5)
		self.assertEquals(w.url, "NOW")
		

	def test_run_many(self):
		" Test that the run adds returned work units back into the queue. "
		w = WorkUnit(ManyCommand(), url=1)
		self.q.put(w)
		time.sleep(1.5)
		self.assertEquals(CounterObject.counter, 12)
		CounterObject.counter = 0

	def test_run_exception(self):
		" Test that exceptions in commands do not cause the thread to die. "
		w = WorkUnit(ExceptionCommand())
		self.assertEquals(self.q.put(w), None)

	def test_shutdown(self):
		" Test that the thread shuts down when asked. "
		self.q.put(WorkUnit(shutdown=True))
		time.sleep(0.5)
		self.assertFalse(self.t.is_alive())


if __name__ == '__main__':
	import logging.config
	logging.config.fileConfig('./conf/logging.conf')
	unittest.main()

