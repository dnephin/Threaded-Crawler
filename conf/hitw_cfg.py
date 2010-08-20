"""
Configuration for hitw.

"""


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



ROUTE = [
	FollowA(url = 'http://doubleviking.com/hotties', 
			regex = '.html', chain = [
		FollowIMG(regex = '\.jpg', chain = [
			SaveToFilesystemConditional()
		])
	],
	FollowIMG(url = 'http://doubleviking.com/hotties',
			regex = '\.jpg', chain = [
		SavetoFileSystemConditional()
	])
]
