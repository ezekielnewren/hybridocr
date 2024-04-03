import string
import tensorflow as tf
from PIL import Image
from tensorflow.keras.layers import Input, Conv2D, GlobalAveragePooling2D, MaxPooling2D, Reshape, LSTM, Dense, Dropout, Flatten
import numpy as np
from collections import OrderedDict
from tensorflow.keras import Model
import sympy as sp

class OCREngine:
    def __init__(self):
        self.alphabet = string.ascii_letters + string.digits + string.punctuation
        self.alphabet_map = OrderedDict()
        for i in range(len(self.alphabet)):
            self.alphabet_map[self.alphabet[i]] = i+1

        h, w = 29, 43
        # kernel_size = 3
        # pool_size = 2
        self.model = tf.keras.models.Sequential()
        self.model.add(Input((h, w, 1)))
        self.model.add(Conv2D(filters=32, kernel_size=(3, 4), strides=(1, 1), padding="valid", dilation_rate=(1, 1), activation='relu'))
        # self.model.add(MaxPooling2D(pool_size=(3, 2)))
        self.model.add(Conv2D(filters=64, kernel_size=(4, 3), strides=(1, 1), padding="valid", dilation_rate=(1, 1), activation='relu'))
        # self.model.add(MaxPooling2D(pool_size=(2, 3)))
        self.model.add(Conv2D(filters=128, kernel_size=(2, 2), padding="valid", activation='relu'))
        # self.model.add(MaxPooling2D(pool_size=(pool_size, pool_size)))

        conv_dimension_change = sp.sympify("ceil((i-d*(k-1)*p)/s)")
        conv_eh = sp.sympify("h")
        conv_ew = sp.sympify("w")

        for v in self.model.layers:
            if isinstance(v, Conv2D):
                output = v.output

                filters = v.filters
                kernel_size = v.kernel_size
                padding = v.padding
                dilation_rate = v.dilation_rate
                strides = v.strides

                conv_eh = conv_dimension_change.subs("i", conv_eh)
                conv_eh = conv_eh.subs("d", dilation_rate[0])
                conv_eh = conv_eh.subs("k", kernel_size[0])
                conv_eh = conv_eh.subs("p", 0 if padding == "same" else 1)
                conv_eh = conv_eh.subs("s", strides[0])
                conv_eh = conv_eh.simplify()
                conv_ehl = sp.lambdify("h", conv_eh)

                def lh(q):
                    return int(conv_ehl(q))

                conv_ew = conv_dimension_change.subs("i", conv_ew)
                conv_ew = conv_ew.subs("d", dilation_rate[1])
                conv_ew = conv_ew.subs("k", kernel_size[1])
                conv_ew = conv_ew.subs("p", 0 if padding == "same" else 1)
                conv_ew = conv_ew.subs("s", strides[1])
                conv_ew = conv_ew.simplify()
                conv_ewl = sp.lambdify("w", conv_ew)

                def lw(q):
                    return int(conv_ewl(q))

                assert v.output.shape[1] == lh(h)
                assert v.output.shape[2] == lw(w)
                pass
            elif isinstance(v, MaxPooling2D):

                pass


        # [
        #     Input((h, w, 1)),
        #     Conv2D(filters=32, kernel_size=(kernel_size, kernel_size), padding="same", activation='relu'),
        #     MaxPooling2D(pool_size=(pool_size, pool_size)),
        #     Conv2D(filters=64, kernel_size=(kernel_size, kernel_size), padding="same", activation='relu'),
        #     MaxPooling2D(pool_size=(pool_size, pool_size)),
        #     Conv2D(filters=128, kernel_size=(kernel_size, kernel_size), padding="same", activation='relu'),
        #     MaxPooling2D(pool_size=(pool_size, pool_size)),
        #     Reshape((-1, filters * h // pool_size)),
        #     LSTM(128, return_sequences=True),
        #     Dense(128, activation="relu"),
        #     Dropout(0.2),
        #     Dense(1 + len(self.alphabet))  # the 1 is the blank symbol
        # ])
        self.translate_width = lambda v: v // 2

    def to_label(self, word: str):
        return [self.alphabet_map[c] for c in word]

    def to_word(self, label: list[int]):
        return "".join([self.alphabet[i-1] for i in label])

    def inference(self, img: Image):
        image = np.ones((28, 15))
        image = image.reshape((1, 28, 15, 1))
        prediction = self.model.predict(image)

        input_length = np.ones(prediction.shape[0]) * prediction.shape[1]
        decoded, _ = tf.nn.ctc_greedy_decoder(
            inputs=tf.transpose(prediction, [1, 0, 2]),
            sequence_length=input_length,
            merge_repeated=True,
            blank_index=0
        )

        decoded_classes = tf.sparse.to_dense(decoded[0], default_value=-1).numpy()

        return "".join([self.alphabet[i - 1] for i in decoded_classes[0]])

    def train_step(self, data):
        sample, label = data

