"""
 bestjobsca.com
"""

from datetime import datetime, timedelta

from crawler.group import RoutingGroup
from crawler.commands.base import *
from crawler.commands.jobs import *

initial_url = 'http://www.bestjobsca.com/bt-joblist.htm?Bqd=%2BST033&Bqd=&Bqd=%2BTM001&BqdPalabras='
post_regex = re.compile('bt-jobd-.*?\d+.htm', re.IGNORECASE)

route = [
	# Save jobs on page one
	FollowA(url = initial_url, regex = post_regex, chain = [
		StoreToJobDatabase(meta={'region': 'montreal'}),
	]),
	# TODO: following page 
]

ROUTING_GROUP = RoutingGroup('bestjobsca', route)
