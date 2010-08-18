"""
Unit tests for agents.httpagent module.
"""

import unittest
import urllib2
import socket

from agents.httpagent import HttpAgent
from config import GlobalConfiguration


class TestHttpAgent(unittest.TestCase):

	def setUp(self):
		pass

	def tearDown(self):
		GlobalConfiguration.config["HttpAgent"] = {}
		HttpAgent.getAgent().configure()


	def test_init(self):
		" Test that init will not return multi instances. "
		a = HttpAgent.getAgent()
		self.assertRaises(ValueError, HttpAgent)

	def test_configure(self):
		" Test that configure sets config params. "
		GlobalConfiguration.config["HttpAgent"] = {
				'http_timeout': 10,
				'enable_cookies': True,
				'max_retry': 5 }
		a = HttpAgent.getAgent()
		a.configure()

		self.assertEquals(a.http_timeout, 10)
		# TODO: way to check this ? self.assertEquals(a.enable_cookies, True)
		self.assertEquals(a.max_retry, 5)


	def test_getAgent(self):
		"""
		Test that the same agent is returned, and that it does not reconfigure
		itself on each call.
		"""
		a = HttpAgent.getAgent()
		b = HttpAgent.getAgent()
		self.assertEquals(id(a), id(b))

		GlobalConfiguration.config["HttpAgent"] = { 'http_timeout': 99 }
		self.assertEquals(HttpAgent.getAgent().http_timeout, 60)


	def test_fetch(self):
		"""
		Test that fetch handles success and different error codes properly.
		This may fail if some of the test urls are in an unexpected state.
		"""
		a = HttpAgent.getAgent()

		self.assertEquals(a.fetch('http://www.google.ca').code, 200)
		self.assertEquals(type(a.fetch('http://gbogusdomain.com/').message), socket.gaierror)
		self.assertEquals(a.fetch('http://www.google.ca/doesnotexist').code, 404)
		a.http_timeout = 1
		self.assertEquals(a.fetch('http://pontiffx.homeip.net').code, 0)
		# TODO: more error conditions


if __name__ == '__main__':
	import logging.config
	logging.config.fileConfig('./conf/logging.conf')
	unittest.main()
