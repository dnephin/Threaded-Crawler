"""
Stubbed test classes used in different unit tests.
"""

from crawler.threads import WorkUnit
from crawler.commands.base import Command



class SimpleCommand(Command):

	def __init__(self, url=None):
		self.url = url
		Command.__init__(self, [])

	def execute(self, work_unit):
		work_unit.url = "NOW"

class CounterObject(object):

	counter = 0

class ManyCommand(SimpleCommand):

	def execute(self, work_unit):
		if work_unit.url > 5:
			return None
		CounterObject.counter += 1
		c = ManyCommand()
		return [WorkUnit(c, url=work_unit.url+1), WorkUnit(c, url=work_unit.url+2)]

class ExceptionCommand(SimpleCommand):

	def execute(self, work_unit):
		raise ValueError("lalala")



if __name__ == "__main__":
	"""
	Run entire test suite.
	"""

	import unittest
	from test import threads, tcrawler
	from test.agents import httpagent, fsagent
	from test.commands import base, image
	
	import logging.config
	logging.config.fileConfig('./conf/logging.conf')
	
	# alias
	l = unittest.defaultTestLoader.loadTestsFromModule
	
	# load tests from modules
	suite = unittest.TestSuite([
		l(threads), 
		l(httpagent),
		l(tcrawler),
		l(fsagent),
		l(base),
		l(image)
	])
	
	# run
	unittest.TextTestRunner().run(suite)
	
	
