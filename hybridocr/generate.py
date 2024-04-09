from tqdm import tqdm

from hybridocr.engine import OCREngine
from hybridocr.core import *
from pathlib import Path
import numpy as np
from collections import OrderedDict
import random
import tensorflow as tf
import time
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

    def __len__(self):
        return len(self.wordlist)*len(self.font_map)

    def __getitem__(self, idx):
        q, r = divmod(idx, len(self.font_map))
        word = self.wordlist[q]
        m = self.font_map[r]
        return np.concatenate([m[c] for c in word], axis=1), word

    def font_example(self):
        for k in self.font_map:
            yield draw_word(k, self.font_map[k]["font"], self.font_height), k


class TextToImageIterator:
    def __init__(self, _generator: TextToImageGenerator, _global_range, _local_range, batch_size, seed, translate_width, word_to_label):
        self.index = None
        self.generator = _generator
        self.global_range = _global_range
        self.local_range = _local_range or (0, self.global_range[1]-self.global_range[0])
        self.batch_size = batch_size
        self.set_seed(seed)
        self.translate_width = translate_width
        self.word_to_label = word_to_label

    def set_seed(self, seed):
        self.index = [i for i in range(self.global_range[0], self.global_range[1])]
        if seed is not None:
            random.seed(seed)
            random.shuffle(self.index)

    def __len__(self):
        return len(self.index)

    def batches(self):
        return (len(self)+(self.batch_size-1))//self.batch_size

    def stream(self):
        for i in range(self.local_range[0], self.local_range[1], self.batch_size):
            sample, label = [], []

            length = min(self.batch_size, len(self)-i)
            for j in range(i, i+length):
                x, word = self.generator[self.index[j]]
                sample.append(x)

                y = self.word_to_label(word)
                label.append(y)

            sample_max_len = max([int(v.shape[1]) for v in sample])
            label_max_len = max([len(v) for v in label])+2

            indices = []
            values = []
            for j in range(length):
                sample_len = sample[j].shape[1]
                sample[j] = pad_array(sample[j], self.generator.font_height, sample_max_len)
                for k in range(len(label[j])):
                    indices.append([j, k])
                    values.append(label[j][k])

                indices.append([j, label_max_len-2])
                values.append(len(label[j]))

                indices.append([j, label_max_len-1])
                values.append(self.translate_width(sample_len))
            sample = np.stack(sample)
            sample = sample.reshape(sample.shape + (1,))

            label = tf.sparse.SparseTensor(indices=indices, values=values, dense_shape=(length, label_max_len))

            if sample.shape[0] != label.shape[0]:
                raise ValueError("first dimension does not match")

            yield sample, label

    def dataset(self):
        return tf.data.Dataset.from_generator(self.stream, output_signature=(
            tf.TensorSpec(shape=(None, self.generator.font_height, None, 1), dtype=tf.float32),
            tf.SparseTensorSpec(shape=(None, None), dtype=tf.int32)
        ))

    @staticmethod
    def loss(y_true, y_pred):
        label = tf.sparse.to_dense(y_true)
        label_len = tf.cast(label[:, -2], tf.int32)
        sample_len = tf.cast(label[:, -1], tf.int32)

        y_true = tf.sparse.SparseTensor(
            indices=y_true.indices,
            values=tf.cast(y_true.values, tf.int32),
            dense_shape=y_true.dense_shape
        )

        logits_time_major = True
        if logits_time_major:
            y_pred = tf.transpose(y_pred, [1, 0, 2])

        return tf.nn.ctc_loss(
            labels=y_true,
            logits=y_pred,
            label_length=label_len,
            logit_length=sample_len,
            logits_time_major=logits_time_major,
            blank_index=0
        )
