"""
 Command objects that relate to image saving.

 These Commands are responsible for executing a task on a ProcessingThread
 given a WorkUnit object.
"""

import logging
import ImageFile
import urlparse

log = logging.getLogger("Command")



#TODO : the image store command





class ImageSaveRule(Rule):
	" Generic thread to save content "
	
	# TODO: move to config
	MIN_WIDTH = 250
	MIN_HEIGHT = 300

	def process(self, resp_item):
		from_tag = resp_item.qitem.from_tag
		if (from_tag == None or from_tag.lower() != 'img') and \
							resp_item.qitem.url[-4:] != '.jpg':
			log.info('Skipping, %s not from img tag (%s).' % (
					resp_item.qitem.url, from_tag))
			return None
		imgParser = ImageFile.Parser()
		try:
			imgParser.feed(resp_item.content)
			image = imgParser.close()
		except IOError, err:
			log.warn("IOError on image: %s:%s" % (resp_item.qitem.url, err))
			return None
		
		size = image.size
		if size[0] < self.MIN_WIDTH or size[1] < self.MIN_HEIGHT:
			log.info("Skipping, image does not meet requirements %d,%d" % (size[0], size[1]))
			return None

		return self._save(resp_item.content, resp_item.qitem.url, resp_item.qitem.site_name)

	def _save(self, content, url, name):
		" save the content "
		url_parts = urlparse.urlparse(url)
		full_name = "%s/%s/%s" % (self.config['save_dir'], name, os.path.basename(url_parts.path))
		# TODO: work with png and gifs
		if full_name[-4:] != '.jpg':
			full_name = "%s/%s.jpg" % (os.path.dirname(full_name), random.randint(100000,999999))
		try:
			fh = open(full_name, 'w')
			fh.write(content)
			fh.close()
		except IOError, err:
			log.warn("Failed saving '%s' from '%s:%s'" % (full_name, url, err))
