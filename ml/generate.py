from PIL import Image, ImageDraw, ImageFont
import time
from core import *
import sys
from pathlib import Path
import json
import cbor2
import numpy as np

from collections import OrderedDict

# font_path = "/usr/share/fonts/liberation-serif/LiberationSerif-Regular.ttf"

file_config = Path(sys.argv[1])

with open(file_config) as fd:
    config = json.loads(fd.read())

with open(config["dictionary"]) as fd:
    dictionary = [v.rstrip() for v in fd.readlines()]

longest_word = max([len(v) for v in dictionary])

character_set = set()
for word in dictionary:
    for c in word:
        character_set.add(c)
t = [c for c in character_set]
t.sort()
character_set = "".join(t)


font_height = 28
pad = 5

train = OrderedDict()

method = 0

for font_path in config["font"]:
    font = None
    for font_size in range(1, 50+1):
        font = ImageFont.truetype(font_path, font_size)
        text_width, text_height = font.getsize(character_set)
        if text_height > font_height:
            font = ImageFont.truetype(font_path, font_size-1)
        elif text_height == font_height:
            break

    font_map = dict()
    for c in character_set:
        img = draw_word(c, font, font_height)
        font_map[c] = np.array(img) / 255.0

    # alphabet = [font_map[c] for c in character_set]
    # alphabet = np.concatenate(alphabet, axis=1)
    # alphabet *= 255.0
    # alphabet = alphabet.astype(np.uint8)
    # image = Image.fromarray(alphabet)
    # show_image(image)

    beg = time.time()
    if method == 0:

        for word in dictionary:
            print(word)
            t = [font_map[c] for c in word]
            w = np.concatenate(t, axis=1)
    elif method == 1:
        for word in dictionary:
            print(word)
            image = draw_word(word, font)
    elapsed = time.time()-beg
    print("rate:", float(len(dictionary))/elapsed)

    dump = cbor2.dumps(train)

    break


