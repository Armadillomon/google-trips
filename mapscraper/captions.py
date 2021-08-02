import os
import datetime
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

class Caption:
	def __init__(self, caption: str, font: os.PathLike, size: int, padding: int, fill=(255, 255, 255), stroke_width=2, stroke_fill=(0, 0, 0)) -> None:
		self.caption = caption
		self.size = size
		self.font = ImageFont.truetype(font, size)
		self.padding = padding
		self.fill = fill
		self.stroke_width = stroke_width
		self.stroke_fill = stroke_fill

	def add_to_img(self, image: Image.Image, position: tuple):
		draw = ImageDraw.Draw(image)
		self.position = position
		self.length = draw.textlength(self.caption, self.font)
		self.bbox = draw.textbbox(position, self.caption, self.font, "ls", stroke_width=self.stroke_width)
		draw.text(position, self.caption, self.fill, self.font, "ls", stroke_width=self.stroke_width, stroke_fill=self.stroke_fill)

class DateCaption(Caption):
	DATE_FORMAT = "%Y-%m-%d"

	def __init__(self, date: datetime.date, *args, **kwargs):
		self.date = date
		caption = date.strftime(self.DATE_FORMAT)
		super().__init__(caption, *args, **kwargs)

	def add_to_img(self, image: Image.Image, position: tuple = None):
		if position is None:
			position = (self.padding, image.size[1] - self.padding)
		super().add_to_img(image, position)

class AnnotationSymbol:
	def __init__(self, path: os.PathLike):
		self.image = Image.open(path)
		self.size = self.image.size

	def __del__(self):
		self.close()

	def add_to_img(self, image: Image.Image, position: tuple):
		image.alpha_composite(self.image, position)

	def close(self):
		self.image.close()