"""
Unit tests for threads class of the tcrawler.
"""

import unittest
from threads import ProcessingThread, WorkUnit
from Queue import Queue
from threading import Semaphore
from commands.base import Command
import time


class SimpleCommand(Command):

	def __init__(self):
		Command.__init__(self, [])

	def execute(self, work_unit):
		work_unit.url = "NOW"

class ManyCommand(SimpleCommand):

	def execute(self, work_unit):
		if work_unit.url > 5:
			return None
		print work_unit.url
		c = ManyCommand()
		return [WorkUnit(c, url=work_unit.url+1), WorkUnit(c, url=work_unit.url+2)]


class TestProcessingThread(unittest.TestCase):

	def setUp(self):
		self.q = Queue()
		self.s = Semaphore(1)
		self.t = ProcessingThread(self.q, self.s)

	def tearDown(self):
		self.q.put(WorkUnit(shutdown=True))
		self.t.join()
		self.q.join()


	def test_start_stop_working(self):
		"""
		Test that start_working and stop_working properly alter the semaphore.
		"""
		self.t.start_working()
		self.assertEquals(self.s._Semaphore__value, 0)
		self.t.stop_working()
		self.assertEquals(self.s._Semaphore__value, 1)


	def test_run(self):
		" Test that the thread runs the execute of command. "
#		w = WorkUnit(SimpleCommand())
#		self.q.put(w)
#		time.sleep(0.5)
#		self.assertEquals(w.url, "NOW")
		

	def test_run_many(self):
		" Test that the run adds returned work units back into the queue. "
		# TODO: better way to test this
		#w = WorkUnit(ManyCommand(url=1))
		#time.sleep(3)

	def test_run_exception(self):
		pass

	def test_shutdown(self):
		pass


if __name__ == '__main__':
	import logging.config
	logging.config.fileConfig('./conf/logging.conf')
	unittest.main()

