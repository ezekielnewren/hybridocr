import math
import os
import struct
import time
import json
import sys

from tqdm import tqdm

from hybridocr.engine import OCREngine
from hybridocr.generate import TextToImageGenerator, TextToImageIterator
from pathlib import Path
from fontTools.ttLib import TTFont
from hybridocr.core import *
import tensorflow as tf


def go0():
    engine = OCREngine()

    dir_home = Path(sys.argv[1])
    batch_size = int(sys.argv[2])

    file_config = dir_home / "config.json"

    beg = time.time()
    with open(file_config) as fd:
        config = json.loads(fd.read())

    # dictionary = [string.ascii_letters + string.digits + string.punctuation]
    dir_wordlist = dir_home / "wordlist"
    file_dictionary = dir_wordlist / config["dictionary"]
    with open(file_dictionary) as fd:
        dictionary = [v.rstrip() for v in fd.readlines()]

    generator = TextToImageGenerator(dir_home, engine.alphabet, dictionary, config["font"], engine.height)
    elapsed = time.time() - beg
    print("time to initialize:", elapsed)

    count = 0
    beg = time.time()

    file_model = dir_home/"model.keras"

    dist = split_distribution([.75, .25], len(generator))
    it = TextToImageIterator(generator, dist[0], batch_size, None, engine.translate_width, engine.to_label)

    # for sample, label in it.stream():
    #     logits = engine.model(sample)
    #     TextToImageIterator.loss(label, logits)

    engine.model.compile(optimizer="adam", loss=TextToImageIterator.loss)

    for epoch in range(5):
        engine.model.fit(x=it.dataset(), y=None, batch_size=batch_size, epochs=1,
                         steps_per_epoch=int(math.ceil(len(it) / batch_size)))
        random_bytes = os.urandom(8)
        seed = struct.unpack("Q", random_bytes)[0]
        it.set_seed(seed)

    elapsed = time.time() - beg
    print("total time:", elapsed)
    print("rate:", float(count) / elapsed)


def go1():
    dir_home = Path(sys.argv[1])
    file_config = dir_home / "config.json"

    beg = time.time()
    with open(file_config) as fd:
        config = json.loads(fd.read())

    for v in config["font"]:
        path = dir_home / "fonts" / v

        font = TTFont(path)
        print(path.name)
        for axis in font['fvar'].axes:
            print("   ", axis.axisTag)

    pass


def main():
    go0()


if __name__ == "__main__":
    main()
