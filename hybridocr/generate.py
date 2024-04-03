from tqdm import tqdm

from hybridocr.engine import OCREngine
from hybridocr.core import *
from pathlib import Path
import numpy as np
from collections import OrderedDict
import tensorflow as tf
import os


class TextToImageGenerator:
    def __init__(self, _dir_home, _alphabet, _wordlist, _font_selection: list, _font_height):
        self.dir_home = Path(_dir_home)
        self.alphabet = _alphabet
        self.wordlist = _wordlist
        self.font_selection = _font_selection
        self.font_height = _font_height

        file_font_cache = self.dir_home / "fonts.cbor.gz"

        if not file_font_cache.exists():
            self.font_cache = OrderedDict()
            data = cbor_save(self.font_cache)
            save_to_file_with_rename(self.dir_home, file_font_cache.name, data)

        with open(file_font_cache, "rb") as fd:
            self.font_cache = cbor_load(fd.read())

        change = 0
        if self.font_height not in self.font_cache:
            self.font_cache[self.font_height] = OrderedDict()
            change += 1

        font_path = []
        for root, dirs, files in os.walk(self.dir_home/"fonts"):
            for file in files:
                t = Path(root)/file
                if t.is_file() and str(t).endswith("ttf"):
                    font_path.append(file)
        font_path.sort()

        for font_name in font_path:
            if font_name in self.font_cache[self.font_height]:
                continue
            path = str(self.dir_home / "fonts" / font_name)
            for font_size in range(1, 50 + 1):
                try:
                    font = ImageFont.truetype(path, font_size)
                except OSError as e:
                    if e.args[0] == "invalid pixel size":
                        continue
                    raise e
                _, _, text_width, text_height = font.getbbox(self.alphabet)
                if text_height > self.font_height:
                    font_size -= 1

                if text_height >= self.font_height:
                    self.font_cache[self.font_height][font_name] = OrderedDict()
                    self.font_cache[self.font_height][font_name]["size"] = font_size
                    change += 1
                    break

        for font_name in self.font_cache[self.font_height]:
            v = self.font_cache[self.font_height][font_name]
            if "symbol" in v:
                continue

            change += 1
            path = str(self.dir_home / "fonts" / font_name)
            font = ImageFont.truetype(path, v["size"])

            v["symbol"] = OrderedDict()
            for c in self.alphabet:
                w = draw_word(c, font, self.font_height)
                obj = {
                    "size": w.size,
                    "data": w.tobytes()
                }
                # arr = np.array(w) / 255.0
                v["symbol"][c] = obj

        if change > 0:
            data = cbor_save(self.font_cache)
            save_to_file_with_rename(self.dir_home, file_font_cache.name, data)

        self.font_map = OrderedDict()
        for i, font_name in enumerate(self.font_selection):
            v = self.font_cache[self.font_height][font_name]
            for c in v["symbol"]:
                obj = v["symbol"][c]
                img = Image.frombytes("L", obj["size"], obj["data"])
                arr = image_to_array(img)
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

    def font_example(self):
        for k in self.font_map:
            yield draw_word(k, self.font_map[k]["font"], self.font_height), k

    def fit(self, engine: OCREngine, epoch, batch_size=2048):
        optimizer = tf.keras.optimizers.Adam()
        for e in range(epoch):
            length = self.image_generator_len()
            for i in tqdm(range(0, length, batch_size)):
                sample = []
                sample_len = []
                # label = []
                indicies = []
                values = []
                label_len = []
                for j in range(min(batch_size, length-i)):
                    x, word = self.example(i+j)
                    y = engine.to_label(word)

                    sample.append(x)
                    sample_len.append(x.shape[1])

                    indicies += [[j, k] for k in range(len(y))]
                    values += y
                    label_len.append(len(y))

                sample_max_len = max(sample_len)
                label_max_len = max(label_len)

                for j in range(len(sample)):
                    sample[j] = pad_array(sample[j], self.font_height, sample_max_len)
                    sample_len[j] = sample_len[j]//2
                    pass

                label = tf.sparse.SparseTensor(indices=indicies, values=values, dense_shape=(batch_size, label_max_len))

                feed = np.stack(sample)
                feed = feed.reshape((feed.shape[0], feed.shape[1], feed.shape[2], 1))

                with tf.GradientTape() as tape:
                    y_pred = engine.model(feed, training=True)
                    y_pred = tf.transpose(y_pred, [1, 0, 2])

                    loss = tf.nn.ctc_loss(
                        labels=label,
                        logits=y_pred,
                        label_length=label_len,
                        logit_length=sample_len,
                        logits_time_major=True,
                        blank_index=0
                    )

                g = tape.gradient(loss, engine.model.trainable_variables)
                optimizer.apply_gradients(zip(g, engine.model.trainable_variables))

                pass
        pass

