import os
import subprocess

class VideoEncoder:
	def __init__(self, imagedir, format="%06d.png"):
		self.imagedir = imagedir
		self.format = format

	def encode(self, outfile, resolution, framerate, options, override_arguments=False):
		if not override_arguments: options = ["-f", "image2", "-framerate", str(framerate), "-i", os.path.join(self.imagedir, self.format), "-s", resolution, *options]
		subprocess.run(["ffmpeg", *options, outfile], check=True)