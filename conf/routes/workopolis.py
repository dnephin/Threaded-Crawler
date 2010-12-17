"""
Workopolis.com
"""

from datetime import datetime, timedelta

from crawler.group import RoutingGroup
from crawler.commands.base import *
from crawler.commands.jobs import *


yesterday = (datetime.today() - timedelta(days=1)).strftime('%m-%d-%Y')
initial_url = 'http://www.workopolis.com/EN/job-search/montreal-quebec-jobs?l=montreal,quebec&ds=%s&lg=en' % yesterday
post_url = '/EN/job/(\d+)'
next_page_url  = '/EN/job-search/montreal-quebec-jobs\?l=montreal,quebec&ds=%s&lg=en&pn=\d+' % yesterday

job_save = FollowA(regex = post_url, captures = ['id'], chain = [
				StoreToJobDatabase()])

route = [
	# Save jobs on page one
	FollowA(url = initial_url, regex = post_url, captures = ['id'], chain = [
		StoreToJobDatabase(),
	]),

	# follow all other pages from one
	RecursiveFollowA(url = initial_url, regex = next_page_url, text_regex = 'Next', 
			chain = [job_save]),
]


ROUTING_GROUP = RoutingGroup('workopolis', route)
