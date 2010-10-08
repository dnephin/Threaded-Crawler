"""
Configuration for Kijiji.ca
"""
from datetime import datetime, timedelta

from crawler.commands.base import FollowA, FollowAPartial, HttpFetchCommand
from crawler.commands.base import RecursiveFollowA
from crawler.commands.jobs import StoreToJobDatabase

from crawler.agents.httpagent import HttpAgent
from crawler.agents.dbagent import DatabaseAgent

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

__yesterday = (datetime.today() - timedelta(days=1)).strftime('%d-%b-%y')

_initial_url = 'http://montreal.kijiji.ca/f-jobs-W0QQCatIdZ45QQlangZen'
_post_url = 'http://(.*)\.kijiji\.ca/c-jobs-[^W].*'
_next_page_url  = '.*\.kijiji\.ca/f-jobs-W0QQCatIdZ45QQ(?:SortZ2QQ)?PageZ\d+'



__job_save = FollowA(regex = _post_url,
					captures = ['region'],
					chain = [
				StoreToJobDatabase()])


__page_list = FollowA(regex = _next_page_url, text_regex = '\d+', 
					chain = [ __job_save ])
					

ROUTE = [
	# Save jobs on page one
#	FollowA(url = _initial_url, regex = _post_url, captures = ['region'], chain = [
#		StoreToJobDatabase(),
#	]),

	# follow all other pages from one
	RecursiveFollowA(url = _initial_url, regex = _next_page_url, text_regex = 'Next.*', 
			stop_regex = __yesterday, chain = [
		__job_save,
	]),
]
