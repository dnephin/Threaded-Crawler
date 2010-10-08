"""
 Crawler configuration for all montreal sites.
"""
from datetime import datetime, timedelta

from crawler.commands.base import FollowA, FollowAPartial, HttpFetchCommand
from crawler.commands.base import RecursiveFollowA
from crawler.commands.jobs import StoreToJobDatabase

from crawler.agents.httpagent import HttpAgent
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
	job_save = FollowA(regex = post_url, captures = ['region'], chain = [
				StoreToJobDatabase()])

class Kijiji:
	stop_time = (datetime.today() - timedelta(days=1)).strftime('%d-%b-%y')
	initial_url = 'http://montreal.kijiji.ca/f-jobs-W0QQCatIdZ45QQlangZen'
	post_url = 'http://(.*)\.kijiji\.ca/c-jobs-[^W].*'
	next_page_url  = '.*\.kijiji\.ca/f-jobs-W0QQCatIdZ45QQ(?:SortZ2QQ)?PageZ\d+'

	job_save = FollowA(regex = post_url, captures = ['region'], chain = [
				StoreToJobDatabase()])

class Workopolis:
	yesterday = (datetime.today() - timedelta(days=1)).strftime('%m-%d-%Y')
	initial_url = 'http://www.workopolis.com/EN/job-search/montreal-quebec-jobs?l=montreal,quebec&ds=%s&lg=en' % yesterday
	post_url = '/EN/job/(\d+)'
	next_page_url  = '/EN/job-search/montreal-quebec-jobs\?l=montreal,quebec&ds=%s&lg=en&pn=\d+' % yesterday

	job_save = FollowA(regex = post_url, captures = ['id'], chain = [
				StoreToJobDatabase()])
					
class Monster:
	initial_url = 'http://jobsearch.monster.ca/Search.aspx?where=Montreal%2c+Montr%c3%a9al%2c+Quebec&qlt=1355000&qln=1064166&lid=243&tm=1&cy=ca&re=508&k=JobSearchi&pp=100' 
	post_regex = re.compile('http://jobview.monster.ca/.*?Montreal-QC.*', re.IGNORECASE)

class WorkingCa:
	initial_url = 'http://jobs.working.com/careers/jobsearch/results?searchType=advanced&city=Montreal&country=Canada&state=Quebec&location=Montreal,+Quebec&postDate=-1+day&sortBy=postdate&pageSize=1000&view=Brief'
	post_regex = '/careers/jobsearch/detail\?jobId=\d+.*'


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
#	FollowA(url = EmploiQuebec.initial_url, regex = EmploiQuebec.post_url, captures = ['region'], chain = [
#		StoreToJobDatabase()]),
#
#	# follow all other pages from one
#	FollowA(url = EmploiQuebec.initial_url, regex = EmploiQuebec.next_page_url, text_regex = '\d+', chain = [
#		EmploiQuebec.job_save]),
#
#	# recursively follow next batch of pages
#	RecursiveFollowA(url = EmploiQuebec.initial_url, regex = EmploiQuebec.next_page_url, text_regex = 'Next', 
#			chain = [ 
#		EmploiQuebec.job_save, 
#		FollowA(regex = EmploiQuebec.next_page_url, text_regex = '\d+', chain = [ EmploiQuebec.job_save ])
#	]),

	###############		Kijiji				##############
	# Save jobs on page one
#	FollowA(url = Kijiji.initial_url, regex = Kijiji.post_url, captures = ['region'], chain = [
#		StoreToJobDatabase()]),

	# follow all other pages from one
#	RecursiveFollowA(url = Kijiji.initial_url, regex = Kijiji.next_page_url, text_regex = 'Next', 
#			stop_regex = Kijiji.stop_time, chain = [ 
#		Kijiji.job_save]),

	###############		Workopolis			##############
	# Save jobs on page one
#	FollowA(url = Workopolis.initial_url, regex = Workopolis.post_url, captures = ['id'], chain = [
#		StoreToJobDatabase(),
#	]),

	# follow all other pages from one
#	RecursiveFollowA(url = Workopolis.initial_url, regex = Workopolis.next_page_url, text_regex = 'Next', 
#			chain = [Workopolis.job_save]),

	###############		Monster				##############
	# Save jobs on page one
	# Restricts jobs to Montreal proper
#	FollowA(url = Monster.initial_url, regex = Monster.post_regex, chain = [
#		StoreToJobDatabase(meta={'region': 'montreal'}),
#	]),
	# TODO: following page , its done via JS

	###############		Working				 ##############
	FollowA(url = WorkingCa.initial_url, regex = WorkingCa.post_regex, chain = [
		StoreToJobDatabase(meta={'region': 'montreal'})]),
]
