"""
Tests for agents.stats
"""

import unittest


from crawler.agents.stats import Statistics

class TestStatistics(unittest.TestCase):

	def setUp(self):
		self.s = Statistics.getObj()
	
	def test_increment(self):
		" Test that increment adds the proper value, and the details are returned. "
		name = 'who'
		self.s.stat(name)
		self.assertEquals(self.s.details()[name], 1)

		self.s.stat(name, 5)
		self.assertEquals(self.s.details()[name], 6)

	def test_singleton(self):
		" Test that Statistics is a singleton. "
		self.assertEquals(id(self.s), id(Statistics.getObj()))



if __name__ == '__main__':
	import logging.config
	logging.config.fileConfig('./conf/logging.conf')
	unittest.main()


