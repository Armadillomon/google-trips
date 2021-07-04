import os
import json
import argparse
import mapscraper

CONFIG_PATH = "config.json"

if not os.path.exists(CONFIG_PATH):
	f = open(CONFIG_PATH, "w")
	f.write(json.dumps({}))
	f.close()

f = open(CONFIG_PATH, "r")
config = json.loads(f.read())
f.close()
config["profile"] = config.get("profile") or os.path.join(os.getenv("USERPROFILE"), r"AppData\Local\Google\Chrome\User Data")
config["dir"] = config.get("dir") or "maps"
config["ffmpeg_arguments"] = config.get("ffmpeg_arguments", [])
config["ffmpeg_override_arguments"] = config.get("ffmpeg_override_arguments", False)

class ParseResolutionAction(argparse.Action):
	def __init__(self, *args, nargs=None, **kwargs):
		super().__init__(*args, nargs=1, **kwargs)

	def __call__(self, parser, namespace, values, option_string):
		size = self._parse_size(parser, values[0])
		setattr(namespace, "width", size[0])
		setattr(namespace, "height", size[1])

	def _parse_size(self, parser, string):
		try:
			size = string.lower().split("x")
			return (int(size[0]), int("".join(size[1:])))
		except:
			parser.error("invalid resolution")

parser = argparse.ArgumentParser()
parser.add_argument("-n", "--number", required=True, type=int, help="Number of days to save")
parser.add_argument("-s", "--size", action=ParseResolutionAction, required=True, help="Image and video resolution as WxH")
parser.add_argument("-f", "--framerate", type=int, default=1)
parser.add_argument("-p", "--profile", default=config["profile"], help="Google Chrome profile directory")
parser.add_argument("-o", "--output", default=config["dir"], help="Directory where images will be saved")
parser.add_argument("-I", "--images-only", action="store_true", help="Output only images. Do not encode to a video")
parser.add_argument("url", help="URL of the first map to save")
arguments = parser.parse_args()
arguments.ffmpeg_arguments = config["ffmpeg_arguments"]
arguments.ffmpeg_override_arguments = config["ffmpeg_override_arguments"]

scraper = mapscraper.Scraper(arguments)
scraper.scrape(arguments.url, arguments.output, arguments.number)
