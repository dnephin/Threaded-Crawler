"""
 Command objects that relate to image saving.

 These Commands are responsible for executing a task on a ProcessingThread
 given a WorkUnit object.
"""

import logging
import ImageFile
import urlparse
import operator
import urlparse

from crawler.commands.base import StoreCommand
from crawler.agents.fsagent import FileSystemAgent
from common.stats import Statistics

log = logging.getLogger("Command")


class StoreImageToFS(StoreCommand):
	"""
	Store an image to the filesystem if the images properties match
	the conditions specified by this command.
	"""

	def __init__(self, width=None, height=None, type=None, bytes=None):
		"""
		Instantiate the object.

		@param width: a restriction on the width of the image, a positive number
				indicates this value is a minimum, a negative indicates this
				value is a maximum. A tuple of two values indicates a valid
				range for the width, with both values being inclusive.
		@type  width: int or tuple
		@param height: a restriction on the height of the image, (see width param)
		@type  height: int or tuple
		@param type: if set only store images of this content type, also accepts
				a list of types
		@type  type: string or list
		@param bytes: a restriction on the size in bytes of the image (see
				width param).
		@type  bytes: int or tuple
		"""
		self.width_method  = StoreImageToFS._get_value_method(width)
		self.height_method = StoreImageToFS._get_value_method(height)
		self.type_method   = StoreImageToFS._get_value_method(type)
		self.bytes_method  = StoreImageToFS._get_value_method(bytes)


	def content_passes_conditions(self, url, content):
		"""
		Check that the image fits within the criteria specified by this Command.
		"""
		# TODO: skip parsing the image if all conditions are None
		imgParser = ImageFile.Parser()
		try:
			imgParser.feed(content)
			image = imgParser.close()
		except IOError, err:
			log.warn("IOError on image: %s:%s" % (url, err))
			return False

		size = image.size
		if (self.width_method(size[0]) and self.height_method(size[1]) and
				self.type_method(image.format) and self.bytes_method(len(content))):
			return True
		Statistics.getObj().stat('image_did_not_meet_conditions')
		return False

	# TODO: correct filename based on content type
	def build_filename(self, url):
		" Construct the filename from the url. "
		urlparts = urlparse.urlsplit(url)
		return "".join(urlparts[1:4])

	def store(self, url, content, work_unit):
		"""
		Store the content.
		"""
		agent = FileSystemAgent.getAgent()
		fs_return = agent.save(self.build_filename(url), content)
		if not fs_return.result:
			log.warn("Failed to save %s: %s" % (url, fs_return.message))
			Statistics.getObj().stat('image_save_failed')
			return
		Statistics.getObj().stat('image_saved')
		return
		
	@staticmethod
	def _get_value_method(value):
		"""
		Return a function pointer that will evaluate based on the value.

		@param value: some value passed to the constructor
		@type  value: any
		@return: a single param function reference that returns a boolean
		@rtype: function reference

		@raise ValueError: if the type of value is not one of: None, tuple, list,
				string, int
		"""
		if value is None:
			return lambda x: True
		if type(value) == tuple:
			return lambda x: value[0] <= x <= value[1]
		if type(value) == list:
			return lambda x: x in value
		if type(value) == str:
			return lambda x: x == value
		if type(value) == int and value >= 0:
			return lambda x: x >= value
		if type(value) == int and value < 0:
			return lambda x: x <= value
		raise ValueError("Unexpected type '%s' sent to StoreImageToFS with value: %s." % (
				type(value), value))
