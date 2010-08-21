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
		self.dn = "/tcrawwler_unittest_dir_%s" % random.randint(100,500)
		self.fn = "%s/%s" % (self.dn, random.randint(501,999))
		self.random_dir = '/tmp%s' % self.dn
		self.random_file = "/tmp%s" % self.fn

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
		GlobalConfiguration.config[FileSystemAgent] = {
				'base_path': user_path, 
				'on_duplicate': FileSystemAgent.CLOBBER
		}

		self.a.configure()
		self.assertEquals(self.a.base_path, user_path)
		self.assertEquals(self.a.on_duplicate, FileSystemAgent.CLOBBER)

		GlobalConfiguration.config = {}
		self.a.configure()


	def test_build_system_path_and_name(self):
		" Test that build_system_path_and_name builds the proper path and name. "
		path = "/boggus/whatnow"
		file = "newfilename"
		t = self.a.build_system_path_and_name("%s/%s" % (path, file))
		self.assertEquals(t[0], "/tmp%s" % path)
		self.assertEquals(t[1], file)


	def test_backup(self):
		" Test backup creates a proper backup. "
		self.a._backup(self.random_file)
		self.assertFalse(os.path.isfile(self.random_file))

		l = os.listdir(os.path.dirname(self.random_file))
		self.assertEquals(len(l), 1)
		self.assertEquals(l[0][-4:], '.bak')


	def test_save_clobber(self):
		" Test that saving with clobber works. "
		self.a.on_duplicate = self.a.CLOBBER

		s = "asdf123456789"
		r = self.a.save(self.fn, s)
		self.assertTrue(r.result)

		with open(self.random_file) as f:
			self.assertEquals(f.read(), s)

		l = os.listdir(self.random_dir)
		self.assertEquals(len(l), 1)

		self.a.on_duplicate = self.a.SKIP


	def test_save_backup(self):
		" Test that saving with backup works. "
		self.a.on_duplicate = self.a.BACKUP

		s = "asdf123456789"
		r = self.a.save(self.fn, s)
		self.assertTrue(r.result)

		with open(self.random_file) as f:
			self.assertEquals(f.read(), s)

		l = os.listdir(self.random_dir)
		self.assertEquals(len(l), 2)

		self.a.on_duplicate = self.a.SKIP


	def test_save_skip(self):
		" Test that saving with skip works. "
		self.a.on_duplicate = self.a.SKIP

		s = "asdf123456789"
		r = self.a.save(self.fn, s)
		self.assertFalse(r.result)

		with open(self.random_file) as f:
			self.assertNotEquals(f.read(), s)

		l = os.listdir(self.random_dir)
		self.assertEquals(len(l), 1)


	def test_save_file_in_dir_place(self):
		""" Test that a file is removed when in the place of the dir
		and clobber is on."""
	# TODO: Test different paths when file is in place of the dir.



if __name__ == '__main__':
	import logging.config
	logging.config.fileConfig('./conf/logging.conf')
	unittest.main()


