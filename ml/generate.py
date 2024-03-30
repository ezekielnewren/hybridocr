import string

from PIL import Image, ImageDraw, ImageFont
from tqdm import tqdm
import time
from core import *
import sys
from pathlib import Path
import json
import cbor2
import numpy as np
from collections import OrderedDict


class TextToImageGenerator:
    def __init__(self, _wordlist, _font_path: list, _font_height):
        self.wordlist = _wordlist
        self.font_path = _font_path
        self.font_height = _font_height

        self.alphabet = set()
        for word in self.wordlist:
            for c in word:
                self.alphabet.add(c)
        t = [c for c in self.alphabet]
        t.sort()
        self.alphabet = "".join(t)

        self.font_map = OrderedDict()

        for font_path in self.font_path:
            for font_size in range(1, 50 + 1):
                try:
                    font = ImageFont.truetype(font_path, font_size)
                except OSError as e:
                    if e.args[0] == "invalid pixel size":
                        continue
                    raise e
                text_width, text_height = font.getsize(self.alphabet)
                if text_height > self.font_height:
                    font = ImageFont.truetype(font_path, font_size - 1)

                if text_height == self.font_height:
                    self.font_map[font_path] = OrderedDict()
                    self.font_map[font_path]["font"] = font
                    self.font_map[font_path]["symbol"] = OrderedDict()
                    for c in self.alphabet:
                        w = draw_word(c, font, self.font_height)
                        self.font_map[font_path]["symbol"][c] = np.array(w) / 255.0
                    break

    def generate_image_len(self):
        return len(self.wordlist)*len(self.font_map)

    def generate_image(self):
        for word in self.wordlist:
            for m in self.font_map.values():
                yield np.concatenate([m["symbol"][c] for c in word], axis=1), word

    def sample(self):
        for k in self.font_map:
            yield k, draw_word(k, self.font_map[k]["font"], self.font_height)


def main():
    file_config = Path(sys.argv[1])

    with open(file_config) as fd:
        config = json.loads(fd.read())

    with open(config["dictionary"]) as fd:
        dictionary = [v.rstrip() for v in fd.readlines()]

    dictionary.append(string.ascii_letters+string.digits+string.punctuation)

    beg = time.time()
    generator = TextToImageGenerator(dictionary, config["font"], 28)
    elapsed = time.time() - beg
    print("time to initialize:", elapsed)

    count = 0
    beg = time.time()
    for sample, label in tqdm(generator.generate_image(), total=generator.generate_image_len()):
        count += 1
        # print(label)
        # img = array_to_image(array)
        # show_image(img)
        pass

    # for path, img in generator.sample():
    #     count += 1
    #     print(path)
    #     # show_image(img)
    #     pass

    elapsed = time.time() - beg
    print("total time:", elapsed)
    print("rate:", float(count) / elapsed)


if __name__ == "__main__":
    main()


