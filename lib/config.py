"""
 Global configuration utility for singleton agents.

 This module holds a global configuration store, that agents can use to 
 request their configuration objects.  If no object is found, then None
 is returned.

"""



class GlobalConfiguration(object):
	" Stores configuration for any agents. "

	config = {}

	@staticmethod
	def get(name):
		return GlobalConfiguration.get(name, None)
