import re
import locale
import datetime
import time
import io
import os
from selenium import webdriver
from selenium.webdriver.support import expected_conditions
from PIL import Image
import mapscraper.metrics
from .captions import *

class GoogleDateParser:
	PATTERN = r"(\w+),\s+(\d{1,2})\s+(\w+)\s+(\d+)"
	_locale = locale.getdefaultlocale()[0]
	locale.setlocale(locale.LC_TIME, _locale)
	WEEKDAYS = { time.strftime("%A", datetime.date(1970, 1, 4 + i).timetuple()).upper(): i for i in range(0, 7) }
	if _locale == "pl_PL": MONTHS = { "STYCZNIA": 1, "LUTEGO": 2, "MARCA": 3, "KWIETNIA": 4, "MAJA": 5, "CZERWCA": 6, "LIPCA": 7, "SIERPNIA": 8, "WRZEŚNIA": 9, "PAŹDZIERNIKA": 10, "LISTOPADA": 11, "GRUDNIA": 12 }
	else: MONTHS = { time.strftime("%B", datetime.date(1970, 1 + i, 1).timetuple()).upper(): i+1 for i in range(0, 12) }

	@classmethod
	def parse(cls, string):
		result = re.match(cls.PATTERN, string.upper())
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

	def add_date_caption(self, font, size, padding):
		self._date_caption = DateCaption(self.date, font, size, padding)
		self._date_caption.add_to_img(self.image)
	
	def add_annotation(self, type: str, annotation: str or os.PathLike, **kwargs):
		if type == "text":
			font = kwargs["font"]
			size = kwargs["size"]
			padding = size
			caption = Caption(annotation, font, size, padding)
			caption.add_to_img(self.image, (self._date_caption.position[0] + self._date_caption.length, self._date_caption.position[1]))
		elif type == "icon":
			symbol = AnnotationSymbol(annotation)
			symbol.add_to_img(self.image, self._align_symbol(symbol))
		else: raise ArgumentError("Invalid annotation type")

	def _align_symbol(self, symbol: AnnotationSymbol):
		return (self._date_caption.bbox[2], (self._date_caption.bbox[1] + self._date_caption.bbox[3] - symbol.size[1])//2)

	def save(self, filename):
		if os.path.isdir(filename): filename = os.path.join(filename, f"{map.date.strftime('%Y%m%d')}.png")
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
			("zoomin", self.ZOOMIN_SELECTOR),
			("zoomout", self.ZOOMOUT_SELECTOR),
			("toggle_map", self.MAP_SELECTOR),
			("toggle_satellite", self.SATELLITE_SELECTOR)
		)
		self._initialize_overlay(
			self.GOOGLE_ACCOUNT_SETTINGS,
			self.GOOGLE_MAP_SETTINGS,
			self.GOOGLE_ZOOM,
			self.GOOGLE_LAYER
		)

	def _initialize_controls(self, *controls):
		for control in controls:
			self._wait.until(expected_conditions.visibility_of_element_located((webdriver.common.by.By.CSS_SELECTOR, control[1])))
			self.controls[control[0]] = control[1]

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
		return self._driver.find_element_by_css_selector(self.FRAME_SELECTOR).size["width"]

	@property
	def frame_height(self):
		return self._driver.find_element_by_css_selector(self.FRAME_SELECTOR).size["height"]

	def resize_window(self, map_width, map_height):
		window_size = self._driver.get_window_size()
		body_size = self._driver.find_element_by_css_selector("body").size
		correction = [window_size["width"] - body_size["width"], window_size["height"] - body_size["height"]]
		screen = mapscraper.metrics.Screen()
		target_width = map_width + self.frame_width + correction[0]
		target_height = map_height + correction[1]
		if target_width > screen.width or target_height > screen.height: raise RuntimeError("Window cannot be larger than screen resolution")
		self._driver.set_window_size(target_width, target_height)
		canvas = self._driver.find_element_by_css_selector(self.MAP_SELECTOR)
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
		""", self.MAP_CLASS, str(map_width), str(map_height))
		self.controls = MapControls(self._driver)

	def next_map(self):
		next_day = self._wait.until(expected_conditions.element_to_be_clickable((webdriver.common.by.By.CSS_SELECTOR, self.NEXT_SELECTOR)))
		next_day.click()

	@property
	def map(self):
		canvas = self._driver.find_element_by_css_selector(self.MAP_SELECTOR)
		map = GoogleMap.from_bytes(canvas.screenshot_as_png)
		map.date = GoogleDateParser.parse(self._driver.find_element_by_css_selector(self.DATE_SELECTOR).text)
		return map

