"""
 Monster.ca
"""

from datetime import datetime, timedelta

from crawler.group import RoutingGroup
from crawler.commands.base import *
from crawler.commands.jobs import *

initial_url = 'http://jobsearch.monster.ca/Search.aspx?where=Montreal%2c+Montr%c3%a9al%2c+Quebec&qlt=1355000&qln=1064166&lid=243&tm=1&cy=ca&re=508&k=JobSearchi&pp=100' 
post_regex = re.compile('http://jobview.monster.ca/.*?Montreal-QC.*', re.IGNORECASE)

route = [
	# Save jobs on page one
	# Restricts jobs to Montreal proper
	FollowA(url = initial_url, regex = post_regex, chain = [
		StoreToJobDatabase(meta={'region': 'montreal'}),
	]),
	# TODO: following page , its done via JS
]

ROUTING_GROUP = RoutingGroup('monster', route)
