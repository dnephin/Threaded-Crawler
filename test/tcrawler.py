"""
Unit tests for the tcrawler loader.
"""

import unittest
from crawler.tcrawler import Crawler

from test import SimpleCommand

class TestCrawler(unittest.TestCase):


	def setUp(self):
		pass

	def tearDown(self):
		pass


	def test_blank_config_init(self):
		" Test that init method with blank config. "
		c = Crawler([], {}, {})
		self.assertEquals(c.route, [])
		c._shutdown()


	def test_init(self):
		" Test that init loads the configuration. "
		a = SimpleCommand()
		c = Crawler([a, a, a], {'number_threads': 0}, {})
		self.assertEquals(c.route, [a,a,a])
		self.assertEquals(c.config['number_threads'], 0)
		c._shutdown()

	def test_start(self):
		" Test the loader start method. "
		c = Crawler([SimpleCommand()], {'number_threads': 2}, {})
		c.start()
		self.assertTrue(c.work_queue.empty())




if __name__ == '__main__':
	import logging.config
	logging.config.fileConfig('./conf/logging.conf')
	unittest.main()

