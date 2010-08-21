"""
 Commands specific to saveing Job Postings.
"""

import logging

from crawler.commands.base import HttpFetchCommand, Command

from crawler.agents.dbagent import DatabaseAgent
from crawler.agents.stats import Statistics

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
		if not resp:
			return

		if DatabaseAgent.getAgent().save(resp.url, resp.content,
				category=work_unit.meta_data.get('category', None),
				region=work_unit.meta_data.get('city', None)):
			Statistics.getObj().stat('job_saved')
		else:
			Statistics.getObj().stat('job_saved_failed')
			
