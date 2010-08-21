"""
 Unit test for Image Commands.
"""

import unittest
from crawler.commands.image import StoreImageToFS

class TestStoreImageToFS(unittest.TestCase):

	def setUp(self):
		self.c = StoreImageToFS()

	def tearDown(self):
		pass

	def test__get_value_method(self):
		" Test that _get_value_method returns the expected result. "
		# TODO:

	def test_build_filename(self):
		" Test the filename is built properly from a url "
		self.assertEquals(self.c.build_filename(
				'http://example.com/tires/wheels/img.jpg?whatnow'),
				'example.com/tires/wheels/img.jpgwhatnow')

		self.assertEquals(self.c.build_filename(
				'http://example.com/whatimg.gif'),
				'example.com/whatimg.gif')



if __name__ == '__main__':
	import logging.config
	logging.config.fileConfig('./conf/logging.conf')
	unittest.main()


