"""
 Global configuration utility for singleton agents.

 This module holds a global configuration store, that agents can use to 
 request their configuration objects.  If no object is found, then None
 is returned.

"""



class GlobalConfiguration(object):
	" Stores configuration for singleton agents. "

	config = {}

	@staticmethod
	def get(name, default=None):
		"""
		Retrieve configuration based on class name.

		@return: the configuration map for the class with name, or None
		@rtype : dict
		"""
		return GlobalConfiguration.config.get(name, default)
