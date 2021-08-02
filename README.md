# google-trips
Save your Google Maps Timeline to PNG files or make a time-lapse video out of them

Requirements:
- [Python](https://www.python.org/downloads/) 3.9 with [Pillow](https://pillow.readthedocs.io/en/stable/installation.html) 8.2.0 and [Selenium](https://selenium-python.readthedocs.io/installation.html) 3.141.0
- [Google Chrome](https://www.google.com/chrome/) with compatible [WebDriver](https://chromedriver.chromium.org/downloads)
- [ffmpeg](https://ffmpeg.org/download.html) installed and added to PATH

Usage:
trips.py [-h] -n NUMBER [-b BEGIN] -s SIZE [-f FRAMERATE] [-p PROFILE] [-o OUTPUT] [-w] [-I] url

positional arguments:
  url                   URL of the first (oldest) map

optional arguments:
  -h, --help            show this help message and exit
  -n NUMBER, --number NUMBER
                        Number of days to save
  -b BEGIN, --begin BEGIN
                        Begin file numbering from a specific number
  -s SIZE, --size SIZE  Image and video resolution as WxH
  -f FRAMERATE, --framerate FRAMERATE
  -p PROFILE, --profile PROFILE
                        Google Chrome profile directory
  -o OUTPUT, --output OUTPUT
                        Directory where images are saved
  -w, --wait            Wait for user input before starting
  -I, --images-only     Output only images. Do not encode to a video

Example:
trips.py -n 30 -s 800x800 -f 2 https://timeline.google.com/maps/timeline?hl=pl&authuser=(...)&pb=!1m2!1m1!1s2021-06-01