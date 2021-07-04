import time
import os
import mapscraper.encoder
from .google import *

class Scraper:
	def __init__(self, options):
		self.map_width = options.width
		self.map_height = options.height
		self._profile_dir = options.profile
		self._framerate = options.framerate
		self._images_only = options.images_only
		self._ffmpeg_arguments = options.ffmpeg_arguments
		self._ffmpeg_override_arguments = options.ffmpeg_override_arguments

	def scrape(self, url, outdir, n):
		if not os.path.exists(outdir): os.mkdir(outdir)
		window = MapPage(self._profile_dir)
		window.open(url)
		window.resize_window(self.map_width, self.map_height)
		for i in range(1, n+1):
			#window.controls.zoom_in()
			time.sleep(1.5)
			window.resize_map(self.map_width, self.map_height)
			window.controls.hide()
			window.save_map(os.path.join(outdir, f"{i:06d}.png"))
			window.controls.show()
			window.next_map()
		window.close()
		if not self._images_only:
			enc = mapscraper.encoder.VideoEncoder(outdir)
			enc.encode("out.webm", f"{self.map_width}x{self.map_height}", framerate=self._framerate, options=self._ffmpeg_arguments, override_arguments=self._ffmpeg_override_arguments)