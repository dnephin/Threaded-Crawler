"""
Configuration for canadian craigslist sites.


"""

from datetime import datetime, timedelta


AGENT_CONFIG = {

	'JobDatabaseAgent': {
		'host': 	"",
		'dbname': 	"",
		'user': 	"",
		'password': "",
	}


	'HttpAgent' = {
		'http_timeout': 30,	
	
	}


__yesterday = (datetime.today() - timedelta(days=1)).strftime('%a %d %b')

ROUTE = [
	FollowA(url = 'http://geo.craigslist.org/iso/ca', 
			regex = '^http://(\w+)(:?\.en)?\.craigslist\.(:?ca|org|com)/', 
			captures = ['city'], chain = [
		FollowA(regex = '/cgi-bin/jobs.cgi?&category=jjj/', chain = [
			FollowA(regex = '/jjj', chain = [
				FollowAPartial(regex = '/(\w+)/(\d+).html',
						captures = ['category', 'id'],
						stop_regex = __yesterday,
						chain = [
					StoreToJobDatabase(meta = ['city', 'category', 'id', 'content'])
				])
			])
		])
	])
]
