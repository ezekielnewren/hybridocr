import string
import tensorflow as tf
from PIL import Image
from tensorflow.keras.layers import Input, Conv2D, MaxPooling2D, Reshape, Permute, LSTM, Dense, Dropout
import numpy as np
from collections import OrderedDict
from tensorflow.keras import Model
import sympy as sp
from hybridocr.core import *

class OCREngine:
    def __init__(self):
        self.alphabet = string.ascii_letters + string.digits + string.punctuation
        self.alphabet_map = OrderedDict()
        for i in range(len(self.alphabet)):
            self.alphabet_map[self.alphabet[i]] = i+1

        self.height, self.width = 28, None
        self.model = tf.keras.models.Sequential()
        self.model.add(Input((self.height, self.width, 1)))
        self.model.add(Conv2D(filters=32, kernel_size=(3, 3), padding="same", activation='relu'))
        self.model.add(MaxPooling2D(pool_size=(2, 2)))
        self.model.add(Conv2D(filters=64, kernel_size=(3, 3), padding="same", activation='relu'))
        self.model.add(MaxPooling2D(pool_size=(2, 2)))
        # self.model.add(Conv2D(filters=128, kernel_size=(3, 3), padding="valid", activation='relu'))
        # self.model.add(MaxPooling2D(pool_size=(2, 2)))

        conv_dimension_change = sp.sympify("ceil((i-d*(k-1)*p)/s)")
        pool_dimension_change = sp.sympify("floor(i/p)")

        eh = sp.sympify("h")
        ew = sp.sympify("w")

        ehl = sp.lambdify("h", sp.sympify("h"))
        ewl = sp.lambdify("w", sp.sympify("w"))

        def lh(q):
            return int(ehl(q))

        def lw(q):
            return int(ewl(q))

        self.translate_width = lw

        for v in self.model.layers:
            if isinstance(v, Conv2D):
                kernel_size = v.kernel_size
                padding = v.padding
                dilation_rate = v.dilation_rate
                strides = v.strides

                eh = conv_dimension_change.subs("i", eh)
                eh = eh.subs("d", dilation_rate[0])
                eh = eh.subs("k", kernel_size[0])
                eh = eh.subs("p", 0 if padding == "same" else 1)
                eh = eh.subs("s", strides[0])
                eh = eh.simplify()
                ehl = sp.lambdify("h", eh)

                ew = conv_dimension_change.subs("i", ew)
                ew = ew.subs("d", dilation_rate[1])
                ew = ew.subs("k", kernel_size[1])
                ew = ew.subs("p", 0 if padding == "same" else 1)
                ew = ew.subs("s", strides[1])
                ew = ew.simplify()
                ewl = sp.lambdify("w", ew)

                assert v.output.shape[1] == lh(self.height)
                if v.output.shape[2] is not None:
                    assert v.output.shape[2] == lw(self.width)
            elif isinstance(v, MaxPooling2D):
                pool_size = v.pool_size

                eh = pool_dimension_change.subs("i", eh)
                eh = eh.subs("p", pool_size[0])
                eh = eh.simplify()
                ehl = sp.lambdify("h", eh)

                ew = pool_dimension_change.subs("i", ew)
                ew = ew.subs("p", pool_size[1])
                ew = ew.simplify()
                ewl = sp.lambdify("w", ew)

                assert v.output.shape[1] == lh(self.height)
                if v.output.shape[2] is not None:
                    assert v.output.shape[2] == lw(self.width)

        self.model.add(Permute((2, 1, 3)))
        v = self.model.layers[-1]
        self.model.add(Reshape((-1, lh(self.height)*v.output.shape[-1])))
        v = self.model.layers[-1]
        self.model.add(LSTM(128, return_sequences=True))
        v = self.model.layers[-1]
        if v.output.shape[1] is not None:
            assert v.output.shape[1] == lw(self.width)

        self.model.add(Dense(128, activation="relu"))
        self.model.add(Dropout(0.2))
        self.model.add(Dense(1+len(self.alphabet)))

        self.min_pad = 1
        while True:
            if lw(self.min_pad) > 0:
                break
            self.min_pad += 1

        self.model.compile(optimizer="adam")

    def to_label(self, word: str):
        return [self.alphabet_map[c] for c in word]

    def to_word(self, label: list[int]):
        return "".join([self.alphabet[i-1] for i in label])

    def inference(self, arr: Image):
        # arr = image_to_array(img)
        image = arr.reshape((1, arr.shape[0], arr.shape[1], 1))
        logits = self.model(image)
        logits = tf.transpose(logits, [1, 0, 2])
        # prediction = self.model.predict(image)

        input_length = tf.constant([self.translate_width(image.shape[2])])
        decoded, log_prob = tf.nn.ctc_greedy_decoder(
            inputs=logits,
            sequence_length=input_length
        )

        dense_decoded = tf.sparse.to_dense(decoded[0])

        clean = [int(v) for v in dense_decoded[0] if int(v) > 0]

        return "".join([self.alphabet[i - 1] for i in clean])

    def train_step(self, data):
        sample, label = data

