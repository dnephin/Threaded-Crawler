"""
 Crawler configuration for all montreal sites.
"""
from datetime import datetime, timedelta

from crawler.commands.base import FollowA, FollowAPartial, HttpFetchCommand
from crawler.commands.base import RecursiveFollowA
from crawler.commands.jobs import StoreToJobDatabase

from common.agents.httpagent import HttpAgent
from crawler.agents.dbagent import DatabaseAgent

import re


CRAWLER_CONFIG = {
	'number_threads': 5
}


AGENT_CONFIG = {

	DatabaseAgent: {
		'database': 	"raw",
		'user': 		"jobs",
		'password': 	"jobspass",
		'max_conn':		30,
		'min_conn':		6,
	},


	HttpAgent: {
		'http_timeout': 29,
		'enable_cookies': True,
		'cookie_file': '/tmp/crawler_cookie',
		'user_agent': 'Mozilla/5.0 perzoot.com (http://perzoot.com/aboutus)',
	}
}

ROUTING_DIR = './conf/routes'

ROUTE = []
