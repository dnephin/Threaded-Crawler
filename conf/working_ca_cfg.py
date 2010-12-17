"""
Configuration for jobs.working.com canada
"""
from datetime import datetime, timedelta

from crawler.commands.base import FollowA, FollowAPartial, HttpFetchCommand
from crawler.commands.base import RecursiveFollowA
from crawler.commands.jobs import StoreToJobDatabase

from crawler.agents.httpagent import HttpAgent
from crawler.agents.dbagent import DatabaseAgent

import re

CRAWLER_CONFIG = {
	'number_threads': 10
}


AGENT_CONFIG = {

	DatabaseAgent: {
		'database': 	"test_raw",
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


class WorkingCa:
	initial_url = 'http://jobs.working.com/careers/jobsearch/results?searchType=advanced&city=Montreal&country=Canada&state=Quebec&location=Montreal,+Quebec&postDate=-1+day&sortBy=postdate&pageSize=1000&view=Brief'
	post_regex = '/careers/jobsearch/detail\?jobId=\d+.*'


ROUTE = [
	FollowA(url = WorkingCa.initial_url, regex = WorkingCa.post_regex, chain = [
		StoreToJobDatabase(meta={'region': 'montreal'}),
	]),

]
