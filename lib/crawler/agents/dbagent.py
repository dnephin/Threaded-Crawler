"""
 Database storage agent, for saving Job Postings.
"""

import logging
import psycopg2

from crawler.config import GlobalConfiguration
from common.pattern import Singleton

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
		- pass (Default: None)
			- the password to authenticate connect to the database
		- dbname (Default: None)
			- the database name
		- port (Default: None)
			- the port the database server is running on
	"""
	__metaclass__ = Singleton

	def __init__(self):
		self.configure()
		self.do_connect()

	@staticmethod
	def getAgent():
		return DatabaseAgent()

	def configure(self):
		"""
		Configure the DatabseAgent from GlobalConfiguration.
		"""
		self.conf = {}
		conf = GlobalConfiguration.get(self.__class__, {})

		self.conf['host'] = conf.get('host', None)
		self.conf['user'] = conf.get('user', None)
		self.conf['password'] = conf.get('pass', None)
		self.conf['dbname'] = conf.get('dbname', None)
		self.conf['port'] = conf.get('port', None)
#		self.conf['tablename'] = conf.get('tablename', 'raw_posting')


	def do_connect(self):
		""" 
		Connect to the database with the given connection settings.
		"""
		#TODO check what is set
		self.conn = psycopg2.connect(
				database=self.conf['dbname'],
				user=self.conf['user'],
				password=self.conf['password'])
#				host=self.conf['host'],
#				port=self.conf['port'])


	def save(self, url, content, category=None, region=None):
		"""
		Save the record.
		"""
		# TODO: document
		# TODO: error conditions
		try:
			cursor = self.conn.cursor()
			cursor.execute("""
					INSERT into raw_posting(url, content, category, region)
					VALUES(%s, %s, %s, %s)
					""", (url, content, category, region))
			self.conn.commit()
		except Exception, err:
			self.conn.rollback()
			log.warn("[%s] %s: %s" % (url, type(err), err))
			return False
		finally:
			if cursor:
				cursor.close()
		return True
