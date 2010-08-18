"""
 Commands specific to saveing Job Postings.
"""

import logging

from commands.base import HttpFetchCommand, Command


log = logging.getLogger("Command")




class StoreToJobDatabase(HttpFetchCommand):
	" Use the database agent to save a job posting to the database. "
	

	def __init__(self, chain=None, meta=[]):
		self.meta = meta
		Command.__init__(self, chain)

	# TODO: save to database using DBAgent
	def execute(self, work_unit):
		" Fetch the url to save, and store it. "
		resp = self.fetch(work_unit.url)

		print "Save %s, %s" % (work_unit.url, work_unit.meta_data)
#		if resp.success():
#			self.save(resp.content, work_unit.meta_data)
