import string
import random
import time
import json
import sys

from tqdm import tqdm
from engine import OCREngine
from generate import TextToImageGenerator
from pathlib import Path


def main():
    engine = OCREngine()

    dir_home = Path(sys.argv[1])

    file_config = dir_home / "config.json"

    beg = time.time()
    with open(file_config) as fd:
        config = json.loads(fd.read())

    dictionary = [string.ascii_letters + string.digits + string.punctuation]
    with open(config["dictionary"]) as fd:
        dictionary += [v.rstrip() for v in fd.readlines()]

    generator = TextToImageGenerator(dir_home, dictionary, config["font"], 28)
    elapsed = time.time() - beg
    print("time to initialize:", elapsed)

    count = 0
    beg = time.time()

    generator.fit(engine, 1)

    # idx = [i for i in range(generator.image_generator_len())]
    # chunk_size = 100000
    # for epoch in range(1):
    #     t = []
    #     for i in tqdm(idx):
    #         v = generator.example(i)
    #         t.append(v)
    #         if len(t) >= chunk_size:
    #             sample, label = zip(*t)
    #             label = [engine.to_label(v) for v in label]
    #             t.clear()
    #             engine.model.fit(sample, label, 1, 128)
    #         # img = array_to_image(sample)
    #         # show_image(img)
    #         pass
    #     random.shuffle(idx)

    # for i in tqdm(range(generator.image_generator_len())):
    #     sample, label = generator.example(i)
    #     # img = array_to_image(sample)
    #     # show_image(img)
    #     pass

    elapsed = time.time() - beg
    print("total time:", elapsed)
    print("rate:", float(count) / elapsed)


if __name__ == "__main__":
    main()
