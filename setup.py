from setuptools import setup, find_packages

setup(
	name = 'JobsiteCrawler',
	version = '0.3.1',
	packages = find_packages('lib'),
	package_dir = {
		'crawler': 'lib/crawler',
	},
	data_files= [
		('conf', ['./conf']),
	],
	scripts = ['cmd', 'tcrawler'],
	author = 'Perzoot',
	author_email = 'daniel@perzoot.com',
	url = 'crawler.git'

)
