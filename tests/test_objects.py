import pytest

from objects.hub import Hub
from objects.image import App
from objects.image import Image

#test __init__ from objects.hub.Hub
def test_make_hub():
	new_hub = Hub("im", "sorry", "dave")


#test __init__ from objects.image.App
def test_make_app():
	new_app = App("im", "afraid")

	new_app.add_keyword("i")
	assert(len(new_app.keywords) == 1)

	new_app.verify()
	assert(new_app.is_bad == True)


#test __init__ from objects.image.Image
def test_make_image():
	global new_image
	new_image = Image("cant", "let", "you")

	new_image.add_tag("do")
	assert(len(new_image.tags) == 1)

	new_image.add_data("that")
	assert(len(new_image.data) == 1)

	new_image.add_arch("the_game")
	assert(len(new_image.archs) == 1)
