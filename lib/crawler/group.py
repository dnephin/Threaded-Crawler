"""
 Group routes for each site together.
"""

import sys
import os
import logging
import itertools
from imp import load_source

log = logging.getLogger('Groups')



class RoutingGroup(object):
	"""
	A class which encapsulates a group of Commands, and sets itself as the
	group in each, traversing the chain of each.
	"""

	def __init__(self, name, route):
		self.name = name
		self.route = route
		for command in self.route:
			self.recursive_add_self(command)


	def recursive_add_self(self, command):
		"""
		Set this RoutingGroup as the group of the command, and recurse down the
		chain of commands.
		"""
		command.group = self
		if not command.chain:
			return
		for sub_command in command.chain:
			self.recursive_add_self(sub_command)

	@staticmethod
	def load_from_dir(dir):
		"""
		Load RoutingGroups from a directory full of modules. 

		@param dir: the directory name
		@type dir: string
		@return: list of RoutingGroup objects
		@rtype: list
		"""
		try:
			files = os.listdir(dir)
		except OSError, e:
			log.warn('Failed to load modules from dir %s: %s' % dir, e)
			return []

		groups = []

		for py_file in itertools.ifilter(lambda f: f.endswith('.py'), files):
			try:
				path = "%s/%s" % (dir, py_file)
				module = load_source(py_file, path)
			except ImportError, e:
				log.warn('Failed to load config module from %s: %s' % (path, e))
				continue

			if not hasattr(module, 'ROUTING_GROUP'):
				log.warn('Did not find ROUTING_GROUP in %s' % path)
				continue

			groups.append(module.ROUTING_GROUP)
		return groups

