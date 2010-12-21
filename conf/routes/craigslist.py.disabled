"""
Craigslist for Canada
"""

from datetime import datetime, timedelta

from crawler.group import RoutingGroup
from crawler.commands.base import *
from crawler.commands.jobs import *


base_url = 'http://montreal.en.craigslist.ca/jjj/'
stop_time = (datetime.today() - timedelta(days=2)).strftime('%a %d %b')
post_regex = '/(\w+)/(\d+).html'
post_captures = ['category', 'id']


route = [
	FollowA(url = base_url, regex = post_regex, captures = post_captures,
			chain = [StoreToJobDatabase()]),
	RecursiveFollowA(url = base_url, regex = 'index\d{3,4}\.html',
			stop_regex = stop_time, chain = [
		FollowAPartial(regex = post_regex, captures = post_captures,
				stop_regex = stop_time, chain = [StoreToJobDatabase()])]
	)
]

ROUTING_GROUP = RoutingGroup('craigslist', route)
