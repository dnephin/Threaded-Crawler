"""
 Commands specific to saveing Job Postings.
"""

import logging

from crawler.commands.base import HttpFetchCommand, StoreCommand, Command

from crawler.agents.dbagent import DatabaseAgent
from common.stats import Statistics

log = logging.getLogger("Command")




class StoreToJobDatabase(StoreCommand):
	" Use the database agent to save a job posting to the database. "

	def __init__(self, chain=None, meta=[]):
		self.meta = meta
		Command.__init__(self, chain)

	def store(self, url, content, work_unit):
		if DatabaseAgent.getAgent().save(url, content,
				category=work_unit.meta_data.get('category', None),
				region=work_unit.meta_data.get('city', None)):
			Statistics.getObj().stat('job_saved')
		else:
			Statistics.getObj().stat('job_saved_failed')

	def __repr__(self):
		return "%s(chain=%r, meta=%r)" % (self.__class__.__name__, 
				self.chain, self.meta)
			
