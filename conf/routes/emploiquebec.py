"""
EmploiQuebec.net
"""

from crawler.group import RoutingGroup 
from crawler.commands.base import *
from crawler.commands.jobs import *



initial_url = 'http://placement.emploiquebec.net/mbe/ut/rechroffr/listoffr.asp?mtcle=&pp=1&date=1&prov=rechrcle.asp%3Fmtcle%3D%26pp%3D1%26prov%3Derechroffr%252Easp%26date%3D1%26creg%3D06&offrdisptoutqc=2&creg=06&CL=english'
post_url = 'http://placement.emploiquebec.net/mbe/ut/suivroffrs/apercoffr.asp.*creg%3D(\d+).*'
next_page_url  = '/mbe/ut/rechroffr/listoffr\.asp\?NO%5FPAGE=\d+.*'
job_save = FollowA(regex = post_url, captures = ['region'], chain = [
				StoreToJobDatabase()])

route = [
	# Save jobs on page one
	FollowA(url = initial_url, regex = post_url, captures = ['region'], chain = [StoreToJobDatabase()]),

	# follow all other pages from one
	FollowA(url = initial_url, regex = next_page_url, text_regex = '\d+', chain = [job_save]),

	# recursively follow next batch of pages
	RecursiveFollowA(url = initial_url, regex = next_page_url, text_regex = 'Next', chain = [ 
		job_save, FollowA(regex = next_page_url, text_regex = '\d+', chain = [ job_save ])
	]),
]

ROUTING_GROUP = RoutingGroup( 'emploiquebec', route )

