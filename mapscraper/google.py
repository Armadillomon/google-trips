import re
import locale
import datetime
import time
import io
import os
from selenium import webdriver
from selenium.webdriver.support import expected_conditions
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import mapscraper.metrics

class DateCaption:
	DATE_FORMAT = "%Y-%m-%d"

	def __init__(self, date):
		self.date = date
		self.font_size = 64
		self.font = ImageFont.truetype(r"C:\Windows\Fonts\micross.ttf", self.font_size)
		self.padding = 48
		self.fill = (255, 255, 255)
		self.stroke_width = 2
		self.stroke_fill = (0, 0, 0)

	def add_to_img(self, image, special=True):
		caption = self.date.strftime(self.__class__.DATE_FORMAT)
		draw = ImageDraw.Draw(image)
		self._date_bbox = draw.textbbox((self.padding, image.size[1] - self.padding), caption, self.font, "ls", stroke_width=self.stroke_width)
		draw.text((self.padding, image.size[1] - self.padding), caption, self.fill, self.font, "ls", stroke_width=self.stroke_width, stroke_fill=self.stroke_fill)
		if special: self._handle_special_dates(image)

	def _handle_special_dates(self, image):
		emojis = { "boom": "\U0001F4A5", "plane": "\u2708", "dress": "\U0001F457", "luggage": "\U0001F9F3", "broken": "\U0001F494" }
		emoji_files = { "plane": "2708-fe0f.png", "dress": "1f457.png", "luggage": "1f9f3.png", "broken": "1f494.png" }
		special_dates = { datetime.date(2021, 1, 9): emoji_files["plane"], datetime.date(2021, 1, 24): emoji_files["dress"], datetime.date(2021, 4, 19): emoji_files["luggage"], datetime.date(2021, 4, 28): emoji_files["broken"] }
		if self.date in special_dates:
			icon = Image.open(os.path.join(os.getcwd(), "emoji", special_dates[self.date]))
			image.alpha_composite(icon, (self._date_bbox[2], self._align(icon)[1]))
			icon.close()

	def _align(self, image):
		return (self._date_bbox[2], (self._date_bbox[1] + self._date_bbox[3] - image.size[1])//2)

class GoogleDateParser:
	PATTERN = r"(\w+),\s+(\d{1,2})\s+(\w+)\s+(\d+)"
	_locale = locale.getdefaultlocale()[0]
	locale.setlocale(locale.LC_TIME, _locale)
	WEEKDAYS = { time.strftime("%A", datetime.date(1970, 1, 4 + i).timetuple()).upper(): i for i in range(0, 7) }
	if _locale == "pl_PL": MONTHS = { "STYCZNIA": 1, "LUTEGO": 2, "MARCA": 3, "KWIETNIA": 4, "MAJA": 5, "CZERWCA": 6, "LIPCA": 7, "SIERPNIA": 8, "WRZEŚNIA": 9, "PAŹDZIERNIKA": 10, "LISTOPADA": 11, "GRUDNIA": 12 }
	else: MONTHS = { time.strftime("%B", datetime.date(1970, 1 + i, 1).timetuple()).upper(): i+1 for i in range(0, 12) }

	@classmethod
	def parse(cls, string):
		string = string.upper()
		result = re.match(cls.PATTERN, string)
		if result:
			weekday = cls.WEEKDAYS[result[1]]
			day = int(result[2])
			month = cls.MONTHS[result[3]]
			year = int(result[4])
			return datetime.date(year, month, day)
		else: return None

class GoogleMap:
	def __init__(self):
		self.date = None
		self.image = None

	@classmethod		
	def from_bytes(self, png):
		map = self()
		map.image = Image.open(io.BytesIO(png))
		map.size = map.image.size
		return map

	def add_captions(self):
		caption = DateCaption(self.date)
		caption.add_to_img(self.image)

	def save(self, filename):
		self.image.save(filename)

	def close(self):
		self.image.close()

class MapControls:
	ZOOMIN_SELECTOR = "#map > div > div > div:nth-child(13) > div > div > div > button:nth-child(1)"
	ZOOMOUT_SELECTOR = "#map > div > div > div:nth-child(13) > div > div > div > button:nth-child(3)"
	MAP_SELECTOR = "#map > div > div > div:nth-child(16) > div:nth-child(2) > div:nth-child(1) > button"
	SATELLITE_SELECTOR = "#map > div > div > div:nth-child(16) > div:nth-child(2) > div:nth-child(2) > button"
	GOOGLE_ACCOUNT_SETTINGS = "#gb > div"
	GOOGLE_MAP_SETTINGS = "#map > div > div > div:nth-child(16) > div.map-controls-container"
	GOOGLE_ZOOM = "#map > div > div > div:nth-child(13) > div > div"
	GOOGLE_LAYER = "#map > div > div > div:nth-child(16) > div:nth-child(2)"

	def __init__(self, driver):
		self._driver = driver
		self._wait = webdriver.support.wait.WebDriverWait(self._driver, 60)
		self.controls = {}
		self.overlay = []
		self._display = []
		self._initialize_controls(
			("zoomin", self.__class__.ZOOMIN_SELECTOR),
			("zoomout", self.__class__.ZOOMOUT_SELECTOR),
			("toggle_map", self.__class__.MAP_SELECTOR),
			("toggle_satellite", self.__class__.SATELLITE_SELECTOR)
		)
		self._initialize_overlay(
			self.__class__.GOOGLE_ACCOUNT_SETTINGS,
			self.__class__.GOOGLE_MAP_SETTINGS,
			self.__class__.GOOGLE_ZOOM,
			self.__class__.GOOGLE_LAYER
		)

	def _initialize_controls(self, *controls):
		for control in controls:
			self._wait.until(expected_conditions.visibility_of_element_located((webdriver.common.by.By.CSS_SELECTOR, control[1])))
			self.controls[control[0]] = self._driver.find_element_by_css_selector(control[1])

	def _initialize_overlay(self, *selectors):
		for selector in selectors:
			element = self._wait.until(expected_conditions.visibility_of_element_located((webdriver.common.by.By.CSS_SELECTOR, selector)))
			self.overlay.append(element)
			self._display.append(element.value_of_css_property("display"))

	def hide(self):
		self._driver.execute_async_script("""
			var callback = arguments[arguments.length - 1];
			for (element of arguments[0]) element.style.display = "none";
			callback();
		""", self.overlay)

	def show(self):
		self._driver.execute_async_script("""
			var callback = arguments[arguments.length - 1];
			for (index in arguments[0]) arguments[0][index].style.display = arguments[1][index];
			callback();
		""", self.overlay, self._display)

	def zoom_in(self):
		button = self._wait.until(expected_conditions.element_to_be_clickable((webdriver.common.by.By.CSS_SELECTOR, self.controls["zoomin"])))
		button.click()

	def zoom_out(self):
		button = self._wait.until(expected_conditions.element_to_be_clickable((webdriver.common.by.By.CSS_SELECTOR, self.controls["zoomout"])))
		button.click()

	def toggle_map(self):
		button = self._wait.until(expected_conditions.element_to_be_clickable((webdriver.common.by.By.CSS_SELECTOR, self.controls["toggle_map"])))
		button.click()

	def toggle_satellite(self):
		button = self._wait.until(expected_conditions.element_to_be_clickable((webdriver.common.by.By.CSS_SELECTOR, self.controls["toggle_satellite"])))
		button.click()

class MapPage:
	MAP_CLASS = "map-wrapper"
	MAP_SELECTOR = "div.map-wrapper"
	FRAME_SELECTOR = "div.map-page-content-wrapper"
	DATE_SELECTOR = "#map-page > div.map-page-content-wrapper > div > div > div > div.timeline-header > div > div.timeline-title"
	NEXT_SELECTOR = "i.timeline-header-button.next-date-range-button.material-icons-extended.material-icon-with-ripple.rtl-mirrored"

	def __init__(self, profile_dir):
		browser_options = webdriver.ChromeOptions()
		browser_options.add_argument(f"user-data-dir={profile_dir}")
		self._driver = webdriver.Chrome(options=browser_options)

	def open(self, url):
		self._driver.get(url)
		self._wait = webdriver.support.wait.WebDriverWait(self._driver, 60)
		self.controls = MapControls(self._driver)

	def close(self):
		self._driver.close()

	@property
	def frame_width(self):
		return self._driver.find_element_by_css_selector(self.__class__.FRAME_SELECTOR).size["width"]

	@property
	def frame_height(self):
		return self._driver.find_element_by_css_selector(self.__class__.FRAME_SELECTOR).size["height"]

	def resize_window(self, map_width, map_height):
		window_size = self._driver.get_window_size()
		body_size = self._driver.find_element_by_css_selector("body").size
		correction = [window_size["width"] - body_size["width"], window_size["height"] - body_size["height"]]
		screen = mapscraper.metrics.Screen()
		target_width = map_width + self.frame_width + correction[0]
		target_height = map_height + correction[1]
		if target_width > screen.width or target_height > screen.height: raise RuntimeError("Window cannot be larger than screen resolution")
		self._driver.set_window_size(target_width, target_height)
		canvas = self._driver.find_element_by_css_selector(self.__class__.MAP_SELECTOR)
		diff_width = map_width - canvas.size["width"]
		diff_height = map_height - canvas.size["height"]
		if diff_width or diff_height:
			window_size = self._driver.get_window_size()
			self._driver.set_window_size(window_size["width"] + diff_width, window_size["height"] + diff_height)
		self._driver.refresh()
		self.controls = MapControls(self._driver)

	def resize_map(self, map_width, map_height):
		self._driver.execute_async_script("""
			var callback = arguments[arguments.length - 1];
			let canvas = document.getElementsByClassName(arguments[0])[0];
			canvas.style.width = arguments[1] + "px";
			canvas.style.height = arguments[2] + "px";
			callback();
		""", self.__class__.MAP_CLASS, str(map_width), str(map_height))
		self.controls = MapControls(self._driver)

	def next_map(self):
		next_day = self._wait.until(expected_conditions.element_to_be_clickable((webdriver.common.by.By.CSS_SELECTOR, self.__class__.NEXT_SELECTOR)))
		next_day.click()

	def save_map(self, filename):
		canvas = self._driver.find_element_by_css_selector(self.__class__.MAP_SELECTOR)
		map = GoogleMap.from_bytes(canvas.screenshot_as_png)
		map.date = GoogleDateParser.parse(self._driver.find_element_by_css_selector(self.__class__.DATE_SELECTOR).text)
		map.add_captions()
		if os.path.isdir(filename): filename = os.path.join(filename, f"{map.date.strftime('%Y%m%d')}.png")
		map.save(filename)
		map.close()