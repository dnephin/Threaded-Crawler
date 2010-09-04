"""
 Unit test for base Commands.
"""

import unittest
from crawler.commands.base import Command, HttpFollowCommand

class TestHttpFollowCommand(unittest.TestCase):

	def setUp(self):
		pass
	def tearDown(self):
		pass


	def test_init(self):
		" Test init method "
		c = HttpFollowCommand('http://google.com', '\d+', 'This')
		self.assertEquals(c.url, 'http://google.com')

	def test_parse_urls(self):
		c = HttpFollowCommand('http://google.com')

	# TODO: test build_work_units


if __name__ == '__main__':
	import logging.config
	logging.config.fileConfig('./conf/logging.conf')
	unittest.main()



