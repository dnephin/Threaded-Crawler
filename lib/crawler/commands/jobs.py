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

	def __init__(self, *args, **kwargs):
		self.meta = kwargs.pop('meta', {})
		Command.__init__(self, *args, **kwargs)

	def store(self, url, content, work_unit):
		if DatabaseAgent.getAgent().save(url, content,
				category=work_unit.meta_data.get('category', 
						self.meta.get('category', None)),
				region=work_unit.meta_data.get('region', 
						self.meta.get('region', None))):
			self.record('job_saved')
		else:
			self.record('job_saved_failed')

	def __repr__(self):
		return "%s(chain=%r, meta=%r)" % (self.__class__.__name__, 
				self.chain, self.meta)
			
