import time
import os
import mapscraper.encoder
from .google import *

class Scraper:
	ANNOTATION_DATE_FORMAT = "%Y-%m-%d"
	def __init__(self, options):
		self.map_width = options.width
		self.map_height = options.height
		self._profile_dir = options.profile
		self._framerate = options.framerate
		self._images_only = options.images_only
		self._font = options.font
		self._font_size = options.font_size
		self._annotations = options.annotations
		if self._annotations:
			self._annotations_type = options.annotations_type
			self._icon_dir = options.icon_dir
			self._annotation_font = options.annotation_font
			self._annotation_size = options.annotation_size
			self._special_dates = options.special_dates
		self._ffmpeg_arguments = options.ffmpeg_arguments
		self._ffmpeg_override_arguments = options.ffmpeg_override_arguments

	def open(self, url):
		self._window = MapPage(self._profile_dir)
		self._window.open(url)
		self._window.resize_window(self.map_width, self.map_height)

	def scrape(self, outdir, begin, n, annotations=False):
		if not os.path.exists(outdir): os.mkdir(outdir)
		for i in range(begin, begin+n):
			self._window.controls.zoom_in()
			time.sleep(1.5)
			self._window.resize_map(self.map_width, self.map_height)
			self._window.controls.hide()
			map = self._window.map
			map.add_date_caption(font=self._font, size=self._font_size, padding=48)
			if annotations:
				key = map.date.strftime(self.ANNOTATION_DATE_FORMAT)
				if key in self._special_dates:
					value = self._special_dates[key]
					if self._annotations_type == "icon": value = os.path.join(self._icon_dir, value)
					map.add_annotation(self._annotations_type, value, font=self._annotation_font, size=self._annotation_size)
			map.save(os.path.join(outdir, f"{i:06d}.png"))
			map.close()
			self._window.controls.show()
			self._window.next_map()
		self._window.close()
		if not self._images_only:
			enc = mapscraper.encoder.VideoEncoder(outdir)
			enc.encode("out.webm", f"{self.map_width}x{self.map_height}", framerate=self._framerate, options=self._ffmpeg_arguments, override_arguments=self._ffmpeg_override_arguments)