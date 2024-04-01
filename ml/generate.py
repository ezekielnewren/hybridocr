from tqdm import tqdm

from core import *
from pathlib import Path
import numpy as np
from collections import OrderedDict
import tensorflow as tf

from ml.engine import OCREngine


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

    def font_example(self):
        for k in self.font_map:
            yield draw_word(k, self.font_map[k]["font"], self.font_height), k

    def fit(self, engine: OCREngine, epoch):
        optimizer = tf.keras.optimizers.Adam()
        batch_size = 128
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
                    pad = sample_max_len-sample[j].shape[1]
                    pad_tensor = np.ones((self.font_height, pad))
                    sample[j] = np.concatenate([sample[j], pad_tensor], axis=1)
                    sample_len[j] = (sample_len[j]-2)//2
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


def main():
    pass


if __name__ == "__main__":
    main()


