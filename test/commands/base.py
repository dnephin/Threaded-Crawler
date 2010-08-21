"""
 Unit test for base Commands.
"""

import unittest
from crawler.commands.base import Command, HttpFollowCommand

class TestHttpFollowCommand(unittest.TestCase):

	def setUp(self):
		self.c = StoreImageToFS()

	def tearDown(self):
		pass

	# TODO: test parse_urls

	# TODO: test build_work_units


if __name__ == '__main__':
	import logging.config
	logging.config.fileConfig('./conf/logging.conf')
	unittest.main()



