import string
import tensorflow as tf
from PIL import Image
from tensorflow.keras.layers import Input, Conv2D, GlobalAveragePooling2D, MaxPooling2D, Reshape, LSTM, Dense, Dropout, Flatten
import numpy as np
from collections import OrderedDict


class OCREngine:
    def __init__(self):
        self.alphabet = string.ascii_letters + string.digits + string.punctuation
        self.alphabet_map = OrderedDict()
        for i in range(len(self.alphabet)):
            self.alphabet_map[self.alphabet[i]] = i+1

        h, w = 28, None
        filters = 32
        kernel_size = 3
        pool_size = 2
        self.model = tf.keras.models.Sequential([
            Input((h, w, 1)),
            Conv2D(filters=filters, kernel_size=(kernel_size, kernel_size), activation='relu'),
            MaxPooling2D(pool_size=(pool_size, pool_size)),
            Reshape((-1, filters * (h - kernel_size + 1) // pool_size)),
            LSTM(128, return_sequences=True),
            Dense(1 + len(self.alphabet), activation="softmax")  # the 1 is the blank symbol
        ])

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

