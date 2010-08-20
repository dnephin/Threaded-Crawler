"""
Run entire test suite.
"""

import unittest
from test import threads
from test.agents import httpagent

import logging.config
logging.config.fileConfig('./conf/logging.conf')

# alias
l = unittest.defaultTestLoader.loadTestsFromModule

# load tests from modules
suite = unittest.TestSuite([
	l(threads), 
	l(httpagent),
])

# run
unittest.TextTestRunner().run(suite)

