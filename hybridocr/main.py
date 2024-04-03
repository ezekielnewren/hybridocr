import time
import json
import sys

from keras.src.saving.saving_api import save_model

from hybridocr.engine import OCREngine
from hybridocr.generate import TextToImageGenerator
from pathlib import Path
from fontTools.ttLib import TTFont


def go0():
    engine = OCREngine()

    dir_home = Path(sys.argv[1])

    file_config = dir_home / "config.json"

    beg = time.time()
    with open(file_config) as fd:
        config = json.loads(fd.read())

    # dictionary = [string.ascii_letters + string.digits + string.punctuation]
    dir_wordlist = dir_home / "wordlist"
    file_dictionary = dir_wordlist / config["dictionary"]
    with open(file_dictionary) as fd:
        dictionary = [v.rstrip() for v in fd.readlines()]

    generator = TextToImageGenerator(dir_home, engine.alphabet, dictionary, config["font"], 28)
    elapsed = time.time() - beg
    print("time to initialize:", elapsed)

    count = 0
    beg = time.time()

    file_model = dir_home/"model.keras"

    generator.fit(engine, 1)

    # https://www.tensorflow.org/tutorials/keras/save_and_load
    engine.model.save(file_model)

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
