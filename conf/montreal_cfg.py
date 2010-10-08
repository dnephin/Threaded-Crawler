"""
 Crawler configuration for all montreal sites.
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
	}
}

class Craigslist:
	base_url = 'http://montreal.en.craigslist.ca/jjj/'
	stop_time = (datetime.today() - timedelta(days=2)).strftime('%a %d %b')
	post_regex = '/(\w+)/(\d+).html'
	post_captures = ['category', 'id']

class EmploiQuebec:

	initial_url = 'http://placement.emploiquebec.net/mbe/ut/rechroffr/listoffr.asp?mtcle=&pp=1&date=1&prov=rechrcle.asp%3Fmtcle%3D%26pp%3D1%26prov%3Derechroffr%252Easp%26date%3D1%26creg%3D06&offrdisptoutqc=2&creg=06&CL=english'
	post_url = 'http://placement.emploiquebec.net/mbe/ut/suivroffrs/apercoffr.asp.*creg%3D(\d+).*'
	next_page_url  = '/mbe/ut/rechroffr/listoffr\.asp\?NO%5FPAGE=\d+.*'
	job_save = FollowA(regex = EmploiQuebec.post_url, captures = ['region'], chain = [
				StoreToJobDatabase()])


					

ROUTE = [
#	###############		Craigslist			##############
#	FollowA(url = Craigslist.base_url, 
#			regex = Craigslist.post_regex, captures = Craigslist.post_captures,
#			chain = [StoreToJobDatabase()]),
#	RecursiveFollowA(url = Craigslist.base_url, regex = 'index\d{3,4}\.html',
#			stop_regex = Craigslist.stop_time, chain = [
#		FollowAPartial(regex = Craigslist.post_regex, captures = Craigslist.post_captures,
#				stop_regex = Craigslist.stop_time, chain = [StoreToJobDatabase()])]
#	)

	###############		EmploiQuebec		##############
	# Save jobs on page one
	FollowA(url = EmploiQuebec.initial_url, regex = EmploiQuebec.post_url, captures = ['region'], chain = [
		StoreToJobDatabase()])

	# follow all other pages from one
	FollowA(url = EmploiQuebec.initial_url, regex = EmploiQuebec.next_page_url, text_regex = '\d+', chain = [
		EmploiQuebec.job_save]),

	# recursively follow next batch of pages
	RecursiveFollowA(url = EmploiQuebec.initial_url, regex = EmploiQuebec.next_page_url, text_regex = 'Next', 
			chain = [ 
		EmploiQuebec.job_save, 
		FollowA(regex = _next_page_url, text_regex = '\d+', chain = [ EmploiQuebec.job_save ])
	]),
]

