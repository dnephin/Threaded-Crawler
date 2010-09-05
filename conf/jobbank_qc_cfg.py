"""
Configuration for Qubec jobbank.gc.ca sites. (emploisquebec.net)
"""
from datetime import datetime, timedelta
from cookielib import Cookie
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

__yesterday = (datetime.today() - timedelta(days=1)).strftime('%a %d %b')

_initial_url = 'http://placement.emploiquebec.net/mbe/ut/rechroffr/listoffr.asp?mtcle=&pp=1&date=1&prov=rechrcle.asp%3Fmtcle%3D%26pp%3D1%26prov%3Derechroffr%252Easp%26date%3D1%26creg%3D06&offrdisptoutqc=2&creg=06&CL=english'
_post_url = 'http://placement.emploiquebec.net/mbe/ut/suivroffrs/apercoffr.asp.*creg%3D(\d+).*'
_next_page_url  = '/mbe/ut/rechroffr/listoffr\.asp\?NO%5FPAGE=\d+.*'



__job_save = FollowA(regex = _post_url,
					captures = ['region'],
					chain = [
				StoreToJobDatabase()])


__page_list = FollowA(regex = _next_page_url, text_regex = '\d+', 
					chain = [ __job_save ])
					

ROUTE = [
	# Save jobs on page one
	FollowA(url = _initial_url, regex = _post_url, captures = ['region'], chain = [
		StoreToJobDatabase(),
	])

	# follow all other pages from one
	FollowA(url = _initial_url, regex = _next_page_url, text_regex = '\d+', chain = [
		__job_save,
	]),

	# recursively follow next batch of pages
#	RecursiveFollowA(url = _initial_url, regex = _next_page_url, text_regex = 'Next', 
#			chain = [ 
#		__job_save,
#		__page_list 
#	]),
]
