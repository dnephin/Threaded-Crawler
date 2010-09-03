"""
 Database storage agent, for saving Job Postings.
"""

import logging

from crawler.config import GlobalConfiguration
from common.pattern import Singleton
from common.db.connect import ConnectionUtil
from common.db.dao import DocumentDAO
from common.db.objects import HtmlDocument

log = logging.getLogger("DatabaseAgent")


class DatabaseAgent(object):
	"""
	A thread-safe singleton database agent for saving job descriptions 
	to a postgreSQL database.

	Configuration Values:
		- host (Default: None)
			- the hostname of the database
		- user (Default: None)
			- the username to authenticate connect to the database
		- password (Default: None)
			- the password to authenticate connect to the database
		- database (Default: None)
			- the database name
		- port (Default: None)
			- the port the database server is running on
		- min_conn
		- max_conn
	"""
	__metaclass__ = Singleton

	def __init__(self):
		self.configure()

	@staticmethod
	def getAgent():
		return DatabaseAgent()

	def configure(self):
		"""
		Configure the DatabseAgent from GlobalConfiguration.
		"""
		conf = GlobalConfiguration.get(self.__class__, {})
		ConnectionUtil.configure(conf)
		self.dao = DocumentDAO()


	def save(self, url, content, category=None, region=None):
		"""
		Save the record.
		"""
		# TODO: document
		doc = HtmlDocument(url=url, content=content, category=category, 
				region=region)
		self.dao.save([doc])
		return True
