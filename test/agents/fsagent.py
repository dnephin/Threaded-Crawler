"""
Tests for file system agent module.
"""

import unittest
import random
import os
import shutil

from crawler.agents.fsagent import FSOperationResult, FileSystemAgent
from crawler.config import GlobalConfiguration

class TestFileSystemAgent(unittest.TestCase):


	def setUp(self):
		self.a = FileSystemAgent.getAgent()
		self.random_dir = '/tmp/%s' % random.randint(100,999)
		self.random_file = "%s/%s" % (self.random_dir, random.randint(100, 999))

		os.mkdir(self.random_dir)
		f = open(self.random_file, 'w')
		f.write("asdf\n")
		f.close()


	def tearDown(self):
		shutil.rmtree(self.random_dir)


	def test_singleton(self):
		" Test that only instance exists. "
		a = FileSystemAgent.getAgent()
		b = FileSystemAgent.getAgent()
		self.assertEquals(id(a), id(b))

	def test_configuration(self):
		" Test that the configuration is loaded properly. "
		user_path = os.path.expanduser('~')
		GlobalConfiguration.config['FileSystemAgent'] = {
				'base_path': user_path, 
				'on_duplicate': FileSystemAgent.CLOBBER
		}

		self.a.configure()
		self.assertEquals(self.a.base_path, user_path)
		self.assertEquals(self.a.on_duplicate, FileSystemAgent.CLOBBER)


	def test_build_system_path_and_name(self):
		" Test that build_system_path_and_name builds the proper path and name. "
		path = "/boggus/whatnow"
		file = "newfilename"
		t = self.a.build_system_path_and_name("%s/%s" % (path, file))
		self.assertEquals(t[0], "/tmp%s" % path)
		self.assertEquals(t[1], file)

	def test_backup(self):
		" Test backup creates a proper backup. "


	def test_save_clobber(self):
		" Test that saving with clobber works. "


	def test_save_backup(self):
		" Test that saving with backup works. "


	def test_save_skip(self):
		" Test that saving with skip works. "



if __name__ == '__main__':
	import logging.config
	logging.config.fileConfig('./conf/logging.conf')
	unittest.main()


