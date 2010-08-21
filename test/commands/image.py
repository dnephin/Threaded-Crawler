"""
 Unit test for Image Commands.
"""

import unittest
from crawler.commands.image import SaveImageToFS

class TestStoreImageToFS(unittest.UnitTest):

	def setUp(self):
		pass

	def tearDown(self):
		pass


if __name__ == '__main__':
	import logging.config
	logging.config.fileConfig('./conf/logging.conf')
	unittest.main()


