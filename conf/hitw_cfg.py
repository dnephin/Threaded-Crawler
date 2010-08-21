"""
Configuration for hitw.

"""

from crawler.commands.base import FollowA, FollowIMG
from crawler.commands.image import StoreImageToFS
from crawler.agents.fsagent import FileSystemAgent
from crawler.agents.httpagent import HttpAgent


CRAWLER_CONFIG = {
	'number_threads': 25
}


AGENT_CONFIG = {

	FileSystemAgent: {
		'base_path': 	"/tmp/hitw/",
		'on_duplicate': 'BACKUP',
	},


	HttpAgent: {
		'http_timeout': 40,	
	}
}

__store = StoreImageToFS(width=200, height=200)

ROUTE = [
	FollowA(url = 'http://doubleviking.com/hotties/main.php', 
			regex = 'v/[a-zA-Z\d\-_\.]+.jpg.html', chain = [
		FollowIMG(regex = '/hotties/d/.*\.jpg', chain = [
			__store
		])
	]),
]
