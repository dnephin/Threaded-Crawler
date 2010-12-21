"""
 Crawler test run on google.
"""
from datetime import datetime, timedelta

from crawler.commands.base import FollowA, FollowAPartial, HttpFetchCommand
from crawler.commands.base import RecursiveFollowA
from crawler.commands.jobs import StoreToJobDatabase

from common.agents.httpagent import HttpAgent
from crawler.agents.dbagent import DatabaseAgent

import re


CRAWLER_CONFIG = {
	'number_threads': 20
}


AGENT_CONFIG = {

	DatabaseAgent: {
		'database': 	"test_raw",
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

ROUTING_DIR = None

ROUTE = [
	FollowA(url="http://www.google.ca/search?ie=UTF-8&q=pizza",
		regex = "http://.*pizza.*.ca",
		chain = [
			StoreToJobDatabase()
		]
	),
]

