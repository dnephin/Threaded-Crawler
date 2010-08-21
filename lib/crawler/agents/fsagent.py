"""
A singleton thread safe agent for saving files to disk.
"""

from crawler.config import GlobalConfiguration 

import os
import stat
import shutil
import logging
import time

log = logging.getLogger("FileSystemAgent")

class FSOperationResult(object):
	"""
	A data transfer object that identifies the result of a file system operation.
	"""

	def __init__(self, result=False, message=""):
		self.result = result
		self.message = message


class FileSystemAgent(object):
	"""
	A singleton thread-safe agent which saves content to a locally accessible
	file system.

	This agent accepts the following configuration values:
	base_path (Default: /tmp)
			- the root of the path to use when storing files
	on_duplicate (Default: SKIP)
			- the action to take when the file to be saved already exists.
			Possible values: 
			- FileSystemAgent.CLOBBER - write the new file, ignoring the old one
			- FileSystemAgent.BACKUP - create a backup of the old file as .<tstamp>.bak
			- FileSystemAgent.SKIP - do not save the file
	
	"""
	# TODO: do i need a lock for the configure method ?

	__inst = None

	CLOBBER = 1	
	" @cvar: Clobber existing files with the same name. "
	BACKUP  = 2 
	" @cvar: Backup existing files with the same name. "
	SKIP    = 3 
	" @cvar: Skip existing files with the same name. "


	def __init__(self):
		if FileSystemAgent.__inst:
			raise ValueError("Can not create more then one instance, use .getAgent().")
		FileSystemAgent.__inst = self
		self.configure()


	@staticmethod
	def getAgent():
		if not FileSystemAgent.__inst:
			return FileSystemAgent()
		return FileSystemAgent.__inst


	def configure(self):
		" Load the configuration for this agent. "
		conf = GlobalConfiguration.get(self.__class__, {})
		self.base_path = conf.get('base_path', '/tmp')
		self.on_duplicate = conf.get('on_duplicate', FileSystemAgent.SKIP)


	def save(self, filename, content):
		"""
		Save the file to disk, creating directories as needed.

		@param filename: the name of the file with path
		@type  filename: string
		@param content: the contents of the file to write
		@type  content: string
		@return: True if the contents were saved, False otherwise
		@rtype : boolean
		"""
		full_path, name = self.build_system_path_and_name(filename)

		# Ensure that the dir being saved into exists and is a dir
		if not os.path.isdir(full_path):
			if os.path.isfile(full_path):
				if self.on_duplicate == self.CLOBBER:
					log.info("Removing file, its in the way of creating a dir: %s" % full_path)
					os.remove(full_path)
				elif self.on_duplicate == self.BACKUP:
					self._backup(full_path)
				else:
					return FSOperationResult(False, 
							"File in the way of directory creation: %s" % (full_path))
			os.makedirs(full_path)

		full_name = "%s/%s" % (full_path, name)
		if os.path.isfile(full_name):
			if self.on_duplicate == self.CLOBBER:
				log.info("Clobbering file %s" % full_name)
				os.remove(full_name)
			elif self.on_duplicate == self.BACKUP:
				self._backup(full_name)
			else:
				return FSOperationResult(False, "File exists, skipping: %s" % (full_name))
		try:
			fh = open(full_name, 'w')
			fh.write(content)
			fh.close()
		except IOError, err:
			log.warn("Failed saving '%s': %s'" % (full_name, err))
			return FSOperationResult(False, "Failed to save %s: %" % (full_name, err))
		return FSOperationResult(True, "Success")


	def build_system_path_and_name(self, filename):
		"""
		Combine the relative path of filename with base_path and split it from
		the file name.

		@param filename: the relative name and path of the file
		@type  filename: string
		@return:  a two item tuple with the real system path, and the files name
		@rtype : tuple (of strings)
		"""
		full_name = os.path.join(self.base_path, './%s' % filename)
		return os.path.split(os.path.normpath(full_name))



	def _backup(self, path):
		"""
		Backup a file to a new location.

		@param path: the full path to the file to backup
		@type  path: string
		"""
		new_name = "%s.%s.bak" % (path, time.time())
		shutil.move(path, new_name)
