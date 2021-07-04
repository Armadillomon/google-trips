import sys
import ctypes

class Screen:
	def __init__(self):
		if not sys.platform.startswith("win32"): raise RuntimeError("Currently Windows is the only supported platform")
		self._api = ctypes.windll.user32
		self.width = self._api.GetSystemMetrics(0)
		self.height = self._api.GetSystemMetrics(1)