from PIL import Image, ImageDraw, ImageFont
from core import *
import sys
from pathlib import Path
import json

# font_path = "/usr/share/fonts/liberation-serif/LiberationSerif-Regular.ttf"

file_config = Path(sys.argv[1])

with open(file_config) as fd:
    config = json.loads(fd.read())

with open(config["dictionary"]) as fd:
    dictionary = [v.rstrip() for v in fd.readlines()]


font_size = 24

for font_path in config["font"]:
    for word in dictionary:
        img = draw_word(word, font_path, font_size, 28)
        show_image(img)
