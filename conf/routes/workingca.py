"""
 Working.ca
"""


from datetime import datetime, timedelta

from crawler.group import RoutingGroup
from crawler.commands.base import *
from crawler.commands.jobs import *

initial_url = 'http://jobs.working.com/careers/jobsearch/results?searchType=advanced&city=Montreal&country=Canada&state=Quebec&location=Montreal,+Quebec&postDate=-1+day&sortBy=postdate&pageSize=1000&view=Brief'
post_regex = '/careers/jobsearch/detail\?jobId=\d+.*'

route = [
	FollowA(url = initial_url, regex = post_regex, chain = [
		StoreToJobDatabase(meta={'region': 'montreal'})]),
]


ROUTING_GROUP = RoutingGroup('workingcanada', route)
