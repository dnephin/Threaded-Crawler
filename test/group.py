"""
Unit tests for group module.

"""

import unittest
from crawler.group import RoutingGroup


class TestRoutingGroup(unittest.TestCase):


	def test_load_from_dir(self):
		groups = RoutingGroup.load_from_dir('./conf/routes')
		self.assertEquals(2, len(groups))


if __name__ == '__main__':
	import logging.config
	logging.config.fileConfig('./conf/logging.conf')
	unittest.main()

