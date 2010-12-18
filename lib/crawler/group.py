"""
 Group routes for each site together.
"""

import sys
import os.path
import logging
import itertools
import pkgutil

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
		if not os.path.isdir(dir):
			log.warn('Not a valid director for loading config modules: %s' % dir)
			return []
			
		groups = []

		importer = pkgutil.ImpImporter(dir)
		for mod_tuple in importer.iter_modules():
			name = mod_tuple[0]
			mod_loader = importer.find_module(name)
			if not mod_loader:
				continue

			try:
				module = mod_loader.load_module(name)
			except ImportError, e:
				log.warn('Failed to load config module %s: %s' % (name, e))
				continue

			if not hasattr(module, 'ROUTING_GROUP'):
				log.warn('Did not find ROUTING_GROUP in %s' % path)
				continue

			groups.append(module.ROUTING_GROUP)
		return groups

