import random
import string

from tqdm import tqdm
import time
from core import *
import sys
from pathlib import Path
import json
import numpy as np
from collections import OrderedDict


class TextToImageGenerator:
    def __init__(self, _dir_home, _wordlist, _font_path: list, _font_height):
        self.dir_home = Path(_dir_home)
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

        file_font_cache = self.dir_home / "fonts.cbor.gz"

        if not file_font_cache.exists():
            self.font_cache = OrderedDict()
            data = cbor_save(self.font_cache)
            save_to_file_with_rename(self.dir_home, file_font_cache.name, data)

        with open(file_font_cache, "rb") as fd:
            self.font_cache = cbor_load(fd.read())

        if self.font_height not in self.font_cache:
            t = list()
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
                        font_size -= 1

                    if text_height >= self.font_height:
                        x = OrderedDict()
                        x["path"] = font_path
                        x["size"] = font_size
                        t.append(x)
                        break

            self.font_cache[self.font_height] = t

            for v in self.font_cache[self.font_height]:
                font_path = v["path"]
                font_size = v["size"]

                font = ImageFont.truetype(font_path, font_size)

                v["symbol"] = OrderedDict()
                for c in self.alphabet:
                    w = draw_word(c, font, self.font_height)
                    obj = {
                        "size": w.size,
                        "data": w.tobytes()
                    }
                    # arr = np.array(w) / 255.0
                    v["symbol"][c] = obj

            data = cbor_save(self.font_cache)
            save_to_file_with_rename(self.dir_home, file_font_cache.name, data)

        self.font_map = OrderedDict()
        for i, v in enumerate(self.font_cache[self.font_height]):
            for c in v["symbol"]:
                obj = v["symbol"][c]
                img = Image.frombytes("L", obj["size"], obj["data"])
                arr = np.array(img) / 255.0
                v["symbol"][c] = arr
            self.font_map[i] = v["symbol"]

    def image_generator_len(self):
        return len(self.wordlist)*len(self.font_map)

    def image_generator(self):
        for word in self.wordlist:
            for m in self.font_map.values():
                yield np.concatenate([m["symbol"][c] for c in word], axis=1), word

    def example(self, idx):
        q, r = divmod(idx, len(self.font_map))
        word = self.wordlist[q]
        m = self.font_map[r]
        return np.concatenate([m[c] for c in word], axis=1), word

    def iter(self):
        import tensorflow as tf
        inst = self

        class Seq(tf.keras.utils.Sequence):
            def __init__(self, batch_size, shuffle=True):
                self.batch_size = batch_size
                self.shuffle = shuffle
                self.index = [i for i in range(inst.image_generator_len())]

            def __len__(self):
                # Number of batches in the Sequence
                return int(np.ceil(len(self.index) / float(self.batch_size)))

            def __getitem__(self, idx):
                # Fetch a batch of data
                off = idx*self.batch_size
                length = min((idx+1)*self.batch_size, len(self.index))
                # sample = list()
                # label = list()
                x = [inst.example(i) for i in range(off, off+length)]
                # for i in range(off, off+length):
                #     x = inst.example(self.index[i])
                #     sample.append(x[0])
                #     label.append(x[1])
                sample, label = zip(*x)
                return sample, label

            def on_epoch_end(self):
                if self.shuffle:
                    random.shuffle(self.index)

        return Seq(128)

    def font_example(self):
        for k in self.font_map:
            yield draw_word(k, self.font_map[k]["font"], self.font_height), k


def main():
    dir_home = Path(sys.argv[1])

    file_config = dir_home / "config.json"

    beg = time.time()
    with open(file_config) as fd:
        config = json.loads(fd.read())

    dictionary = [string.ascii_letters+string.digits+string.punctuation]
    with open(config["dictionary"]) as fd:
        dictionary += [v.rstrip() for v in fd.readlines()]

    generator = TextToImageGenerator(dir_home, dictionary, config["font"], 28)
    elapsed = time.time() - beg
    print("time to initialize:", elapsed)

    count = 0
    beg = time.time()

    seq = generator.iter()
    for i in tqdm(range(len(seq))):
        batch = seq[i]
        pass

    # for i in tqdm(range(generator.image_generator_len())):
    #     sample, label = generator.example(i)
    #     # img = array_to_image(sample)
    #     # show_image(img)
    #     pass

    # for sample, label in tqdm(generator.image_generator(), total=generator.image_generator_len()):
    #     count += 1
    #     # print(label)
    #     # img = array_to_image(array)
    #     # show_image(img)
    #     pass

    # for img, path in generator.sample():
    #     count += 1
    #     print(path)
    #     # show_image(img)
    #     pass

    elapsed = time.time() - beg
    print("total time:", elapsed)
    print("rate:", float(count) / elapsed)


if __name__ == "__main__":
    main()


