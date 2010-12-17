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
	'number_threads': 20
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

###############		Craigslist			##############
class Craigslist:
	base_url = 'http://montreal.en.craigslist.ca/jjj/'
	stop_time = (datetime.today() - timedelta(days=2)).strftime('%a %d %b')
	post_regex = '/(\w+)/(\d+).html'
	post_captures = ['category', 'id']
#	FollowA(url = Craigslist.base_url, 
#			regex = Craigslist.post_regex, captures = Craigslist.post_captures,
#			chain = [StoreToJobDatabase()]),
#	RecursiveFollowA(url = Craigslist.base_url, regex = 'index\d{3,4}\.html',
#			stop_regex = Craigslist.stop_time, chain = [
#		FollowAPartial(regex = Craigslist.post_regex, captures = Craigslist.post_captures,
#				stop_regex = Craigslist.stop_time, chain = [StoreToJobDatabase()])]
#	)


class Kijiji:
	stop_time = (datetime.today() - timedelta(days=1)).strftime('%d-%b-%y')
	initial_url = 'http://montreal.kijiji.ca/f-jobs-W0QQCatIdZ45QQlangZen'
	post_url = 'http://(.*)\.kijiji\.ca/c-jobs-[^W].*'
	next_page_url  = '.*\.kijiji\.ca/f-jobs-W0QQCatIdZ45QQ(?:SortZ2QQ)?PageZ\d+'

	job_save = FollowA(regex = post_url, captures = ['region'], chain = [
				StoreToJobDatabase()])

class Monster:
	initial_url = 'http://jobsearch.monster.ca/Search.aspx?where=Montreal%2c+Montr%c3%a9al%2c+Quebec&qlt=1355000&qln=1064166&lid=243&tm=1&cy=ca&re=508&k=JobSearchi&pp=100' 
	post_regex = re.compile('http://jobview.monster.ca/.*?Montreal-QC.*', re.IGNORECASE)

class WorkingCa:
	initial_url = 'http://jobs.working.com/careers/jobsearch/results?searchType=advanced&city=Montreal&country=Canada&state=Quebec&location=Montreal,+Quebec&postDate=-1+day&sortBy=postdate&pageSize=1000&view=Brief'
	post_regex = '/careers/jobsearch/detail\?jobId=\d+.*'



	###############		Kijiji				##############
	# Save jobs on page one
#	FollowA(url = Kijiji.initial_url, regex = Kijiji.post_url, captures = ['region'], chain = [
#		StoreToJobDatabase()]),

	# follow all other pages from one
#	RecursiveFollowA(url = Kijiji.initial_url, regex = Kijiji.next_page_url, text_regex = 'Next', 
#			stop_regex = Kijiji.stop_time, chain = [ 
#		Kijiji.job_save]),

	###############		Monster				##############
	# Save jobs on page one
	# Restricts jobs to Montreal proper
#	FollowA(url = Monster.initial_url, regex = Monster.post_regex, chain = [
#		StoreToJobDatabase(meta={'region': 'montreal'}),
#	]),
	# TODO: following page , its done via JS

	###############		Working				 ##############
#	FollowA(url = WorkingCa.initial_url, regex = WorkingCa.post_regex, chain = [
#		StoreToJobDatabase(meta={'region': 'montreal'})]),

