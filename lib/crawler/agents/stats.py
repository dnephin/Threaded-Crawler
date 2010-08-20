"""
 Stats singleton agent.
"""

import threading

class Statistics(object):
	"""
	A singleton thread-safe class which increments stats that are sent to it.
	"""

	__inst = None

	def __init__(self):
		if Statistics.__inst:
			raise ValueError("Only one instance allows, call Statistics.getObj()")
		self._lock = threading.Lock()
		self._store = {}
		Statistics.__inst = self

	@staticmethod
	def getObj():
		"""
		Return the single instance of Statistics object.
		@return: the Statistics singleton
		@rtype:  Statistics
		"""
		if not Statistics.__inst:
			return Statistics()
		return Statistics.__inst


	def stat(self, name, increment=1):
		"""
		Increment the stat by the increment value (1 by default).

		@param name: the name of the stat to increment
		@type  name: string
		@param increment: the value to increment the stat by
		@type  increment: int
		"""
		self._lock.acquire()
		if name not in self._store:
			self._store[name] = 0

		self._store[name] += increment
		self._lock.release()



	def details(self):
		"""
		Return the stats as a dictionary.

		@return: the accumpulated stats.
		@rtype:  dict
		"""
		return self._store


