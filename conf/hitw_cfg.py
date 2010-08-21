"""
Configuration for hitw.

"""

from crawler.commands.base import FollowA, FollowIMG
from crawler.commands.image import StoreImageToFS


CRAWLER_CONFIG = {
	'number_threads': 100
}


AGENT_CONFIG = {

	'FileStoreAgent': {
		'base_path': 	"",
		'on_duplicate_file': 'BACKUP',
	}


	'HttpAgent' = {
		'http_timeout': 30,	
	
	}


__store = StoreImageToFS()

ROUTE = [
	FollowA(url = 'http://doubleviking.com/hotties', 
			regex = '.html', chain = [
		FollowIMG(regex = '\.jpg', chain = [
			__store
		])
	],
	FollowIMG(url = 'http://doubleviking.com/hotties',
			regex = '\.jpg', chain = [
			__store
	])
]
