"""
Configuration for canadian craigslist sites.


"""

from datetime import datetime, timedelta
from commands.base import FollowA, FollowAPartial, HttpFetchCommand, RecursiveFollowA
from commands.jobs import StoreToJobDatabase

from cookielib import Cookie
from datetime import datetime, timedelta

CRAWLER_CONFIG = {
	'number_threads': 30
}


AGENT_CONFIG = {

	'JobDatabaseAgent': {
		'host': 	"",
		'dbname': 	"",
		'user': 	"",
		'password': "",
	},


	'HttpAgent': {
		'http_timeout': 29,
		'enable_cookies': True,
	}
}

__yesterday = (datetime.today() - timedelta(days=1)).strftime('%a %d %b')

__job_save = FollowAPartial(regex = '/(\w+)/(\d+).html',
					captures = ['category', 'id'],
					stop_regex = __yesterday,
					chain = [
				StoreToJobDatabase(meta = ['city', 'category', 'id', 'content'])])

ROUTE = [
	# Hit this url to set the english cookie
	HttpFetchCommand(url = 'http://montreal.en.craigslist.ca/'),
	FollowA(url = 'http://geo.craigslist.org/iso/ca', 
#			regex = '^http://(\w+)(?:\.en)?\.craigslist\.(?:ca|org|com)/', 
			regex = '^http://ottawa(?:\.en)?\.craigslist\.(?:ca|org|com)/', 
			captures = ['city'], chain = [
		FollowA(regex = '/cgi-bin/jobs.cgi\?&(?:amp;)?category=jjj/', chain = [
			FollowA(regex = '/jjj', chain = [ 
				__job_save,
				RecursiveFollowA(regex = 'index\d{3,4}\.html',
						stop_regex = __yesterday,
						chain = [ __job_save ]
				)
			])
		])
	])
]
