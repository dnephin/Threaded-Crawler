"""
Configuration for monster.ca
"""
from datetime import datetime, timedelta

from crawler.commands.base import FollowA, FollowAPartial, HttpFetchCommand
from crawler.commands.base import RecursiveFollowA
from crawler.commands.jobs import StoreToJobDatabase

from crawler.agents.httpagent import HttpAgent
from crawler.agents.dbagent import DatabaseAgent

import re

CRAWLER_CONFIG = {
	'number_threads': 30
}


AGENT_CONFIG = {

	DatabaseAgent: {
		'database': 	"jobs",
		'user': 		"jobs",
		'password': 	"jobspass",
		'max_conn':		100,
		'min_conn':		10,
	},


	HttpAgent: {
		'http_timeout': 29,
		'enable_cookies': True,
		'cookie_file': '/tmp/crawler_cookie',
	}
}


_initial_url = 'http://jobsearch.monster.ca/Search.aspx?where=Montreal%2c+Montr%c3%a9al%2c+Quebec&qlt=1355000&qln=1064166&lid=243&tm=1&cy=ca&re=508&k=JobSearchi&pp=100' 
_post_regex = re.compile('http://jobview.monster.ca/.*?Montreal-QC.*', re.IGNORECASE)


ROUTE = [
	# Save jobs on page one
	FollowA(url = _initial_url, regex = _post_regex, chain = [
		StoreToJobDatabase(meta={'region': 'montreal'}),
	]),

	# TODO: following page , its done via JS
]
