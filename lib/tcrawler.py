"""
 Threaded crawler.
 Prompts for a url, and uses threads to pull content from pages.
"""

import urlparse
import time
from BeautifulSoup import BeautifulSoup
import logging
from Queue import Queue, Empty
import threading
import urllib2
import ImageFile
import os
import random
from socket import timeout
from ssl import SSLError


# logger for crawler module
log = logging.getLogger("ThreadedCrawler")

# Statics
QUEUE_TIMEOUT = 1
HTTP_TIMEOUT = 20
MAX_RETRIES = 3

# TODO: change threads to end on interupt, instead of timeout in poll
# TODO: have status thread be queriable from main input
# TODO: use QueueItem in the queue instead of tuple
# TODO: change logging to config file
# TODO: use parseopts
# TODO: move classes into their own files (run only has parseopts)
"""
TODO:  move specific rules into a config somewhere, to turn into different crawler easily. + add rules
 Requirements:
 	- tags to follow + action rules
	- excluded filename rules (regex list?) + function pointer ?
	- save ruleset
	- etc.
"""

# TODO:  use one http agent (httpAgent class) and keep connection open using urllib3 (connection pool per domain) Must use redirect=False
class HttpAgent(object):
	" Http fetch object. Holds a connection pool for domains. "
	pass


# TODO: move to new file
class Configuration(object):
	" Responsible for parsing the configuration, and creating the rules objects "
	# recurse level, root save dir, default name parsing from url, retries, timeout
	pass

# TODO: move to new file
class Rules(object):
	" Determines which paths to follow, and what content to save "
	pass



class QueueItem(object):
	" A structure to store requests in the queue "
	def __init__(self, url, recurse_level=0, site_name=None, retries_remaining=0, from_tag=None):
		self.url = url
		self.recurse_level = recurse_level
		self.site_name = site_name
		self.retries_remaining = retries_remaining
		self.from_tag = from_tag


class HttpConnThread(threading.Thread):
	" Base class for threads that use http connections "
	def __init__(self, url_set):
		self.url_set = url_set
		self.do_stop = False
		threading.Thread.__init__(self)
		self.start()

	def stop(self):
		self.do_stop = True

class PageThread(HttpConnThread):
	" class for parsing html pages "
	def __init__(self, page_queue, content_queue, url_set):
		self.page_queue = page_queue
		self.content_queue = content_queue
		HttpConnThread.__init__(self, url_set)

	def run(self):
		" run the thread, fetch url "
		while True:
			try:
				recurse_level, url, name, retries = self.page_queue.get(True, QUEUE_TIMEOUT)
			except Empty, err:
				if self.do_stop:
					return
				continue
			log.info("url:%s recurse_level:%d" % (url, recurse_level))

			try:
				resp = urllib2.urlopen(url, timeout=HTTP_TIMEOUT)
				content = resp.read()
			except timeout, err:
				log.warn("Timeout exception on '%s'" % url)
				self.page_queue.task_done()
				if retries:
					self.page_queue.put((recurse_level, url, name, retries-1))
				continue
			except (urllib2.URLError, SSLError, ValueError), err:
				log.warn("UrlError on %s:%s" % (url, err))
				self.page_queue.task_done()
				continue

			log.debug("content size:%d" % (len(content)))
			if recurse_level > 0:
				self.parse_pages(recurse_level-1, content, resp, name)
			self.parse_content(content, resp, name)
			log.debug("task_done")
			self.page_queue.task_done()

	def parse_pages(self, recurse_level, content, resp, name):
		" Parse the html page for more pages "
		url = resp.geturl()
		content = BeautifulSoup(content)
		a_tags = content.findAll('a')
		log.info("Found %d a tags for '%s'" % (len(a_tags), url))
		for a_tag in a_tags:
			# makes sure it contains an image
			img_tags = a_tag.findAll('img')
			if len(img_tags) != 1:
				continue
			try:
				full_url = urlparse.urljoin(url, a_tag['href'])
			except KeyError, err:
				log.warn("No href tag for %s:%s" % (a_tag, err))
			# skip already queued/processed urls
			if full_url in self.url_set:
				continue
			self.page_queue.put((recurse_level, full_url, name, MAX_RETRIES))
			log.debug("adding %s to page queue" % (full_url))


	def parse_content(self, content, resp, name):
		" Parse the html page for content "
		url = resp.geturl()
		content = BeautifulSoup(content)
		img_tags = content.findAll('img')
		log.info("Found %d img tags for '%s'" % (len(img_tags), url))
		for img_tag in img_tags:
			# exclude unlikely images
			img_src = img_tag['src']
			if img_src[-4:] == '.gif':
				continue
			img_url = urlparse.urljoin(url, img_src)
			# skip already queued/processed urls
			if img_url in self.url_set:
				continue
			self.content_queue.put((name, img_url, MAX_RETRIES))
			log.debug("adding %s to image queue" % (img_url))


class SaveThread(HttpConnThread):
	" Generic thread to save content "
	def __init__(self, content_queue, save_dir, url_set):
		self.content_queue = content_queue
		self.save_dir = save_dir.rstrip("/")
		HttpConnThread.__init__(self, url_set)
		
	def run(self):
		" run the thread, pull content from queue "
		while True:
			try:
				name, url, retries = self.content_queue.get(True, QUEUE_TIMEOUT)
			except Empty, err:
				if self.do_stop:
					return
				continue
			log.info("content:%s" % (url,))

			try:
				resp = urllib2.urlopen(url, timeout=HTTP_TIMEOUT)
				content = resp.read()
			except timeout, err:
				self.content_queue.task_done()
				if retries:
					log.warn("Timeout on %s. Adding back to queue." % url)
					self.content_queue.put((name, url, retries-1))
					continue
				log.warn("Giving up on %s. Timedout, and retries maxed." % url)
				continue
			except (urllib2.URLError, SSLError, ValueError), err:
				log.warn("UrlError on %s:%s" % (url, err))
				self.content_queue.task_done()
				continue

			log.debug("content size: %d" % (len(content)))
			if self.check_content(resp, content):
				self.save(resp, content, name)
			log.debug("task done")
			self.content_queue.task_done()
		
	def check_content(self, resp, content):
		" Check if the content passes the requirements for being saved to disk "
		return True

	def save(self, resp, content, name):
		" save the content "
		url_parts = urlparse.urlparse(resp.geturl())
		full_name = "%s/%s/%s" % (self.save_dir, name, os.path.basename(url_parts.path))
		if full_name[-4:] != '.jpg':
			full_name = "%s/%s.jpg" % (os.path.dirname(full_name), random.randint(100000,999999))
		try:
			fh = open(full_name, 'w')
			fh.write(content)
			fh.close()
		except IOError, err:
			log.warn("Failed saving '%s' from '%s:%s'" % (full_name, resp.geturl(), err))


class ImgThread(SaveThread):
	" Class to save images "
	
	MIN_WIDTH = 250
	MIN_HEIGHT = 300

	def check_content(self, resp, content):
		" Check if the image is of required size "
		imgParser = ImageFile.Parser()
		try:
			imgParser.feed(content)
			image = imgParser.close()
		except IOError, err:
			log.warn("IOError on image: %s:%s" % (resp.geturl(), err))
			return False
		
		size = image.size
		if size[0] < self.MIN_WIDTH or size[1] < self.MIN_HEIGHT:
			log.debug("image does not meet requirements %d,%d" % (size[0], size[1]))
			return False
		return image



class StatusThread(threading.Thread):
	def __init__(self, queue_list):
		self.queue_list = queue_list
		threading.Thread.__init__(self)
		self.do_stop = False
		self.start()

	def stop(self):
		self.do_stop = True

	def run(self):
		q_empty = {}
		while True:
			if self.do_stop:
				return
			time.sleep(20)
			for queue in self.queue_list:
				size = queue.qsize()
				log.debug("Queue has %d items." % (size))
				# skip this
				continue
				if size:
					del q_empty[queue]
					continue
				if queue not in q_empty:
					q_empty[queue] = True
					continue
				for i in range(1,500):
					try:
						log.debug("clearning queue %d." % (i))
						queue.task_done()
					except:
						break

	
class Crawler(object):
	""" 
	The web crawler. Setup thread pools, and queues.
	Get user input, and start processing.
	"""
	
	page_threads = 10
	content_threads = 100
	save_dir = "/home/daniel/media/del"

	def __init__(self):
		" Setup resources "
		# Queues of urls to process
		self.page_queue = Queue()
		self.content_queue = Queue()
		# Url set to store already processed urls
		self.url_set = set()
		# processing threads
		self.status_thread = StatusThread([self.page_queue, self.content_queue])
		self.page_thread_pool = []
		self.content_thread_pool = []
		for i in range(self.page_threads):
			self.page_thread_pool.append(PageThread(self.page_queue, self.content_queue, self.url_set))
		for i in range(self.content_threads):
			self.content_thread_pool.append(ImgThread(self.content_queue, self.save_dir, self.url_set))
			

	def start_from_stdin(self):
		" Read url from stdin, and fetch content "
		while True:
			input = raw_input("Enter url, recurse_level, save_name: ")
			if input == "QUIT":
				self.shutdown()
				return
			args = input.split(", ", 2)
			if len(args) < 3:
				print "Missing input arguments."
				continue
			# make the directory
			dir_name = "%s/%s" % (self.save_dir, args[2])
			if not os.path.isdir(dir_name):
				try:
					os.mkdir(dir_name)
				except (IOError,OSError), err:
					log.warn("Error creating dir %s:%s" % (dir_name, err))
					continue

			self.page_queue.put((int(args[1]), args[0], args[2], MAX_RETRIES))
	

	def shutdown(self):
		" end threads "
		for thread in self.page_thread_pool + self.content_thread_pool + [self.status_thread]:
			thread.stop()
		for thread in self.page_thread_pool + self.content_thread_pool + [self.status_thread]:
			thread.join()
			log.debug("Thread shutdown.")


if __name__ == "__main__":
	import sys
	log.setLevel(logging.DEBUG)
	if len(sys.argv) > 1:
		fh = logging.FileHandler(sys.argv[1])
		format = logging.Formatter("[%(threadName)s][%(relativeCreated)d] %(message)s")
		fh.setFormatter(format)
		log.addHandler(fh)
	else:
		log.addHandler(logging.StreamHandler())
	crawler = Crawler()
	crawler.start_from_stdin()
