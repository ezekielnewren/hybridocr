import string
from tensorflow.keras.layers import Input, Conv2D, MaxPooling2D, Reshape, Permute, LSTM, Dense, Dropout
from hybridocr.core import *
from collections import OrderedDict
import tensorflow as tf


class OCREngine:
    def __init__(self):
        self.alphabet = string.ascii_letters + string.digits + string.punctuation
        self.alphabet_map = OrderedDict()
        for i in range(len(self.alphabet)):
            self.alphabet_map[self.alphabet[i]] = i+1

        self.height, self.width = 28, None
        self.model = tf.keras.models.Sequential()
        self.model.add(Input((self.height, self.width, 1)))
        self.model.add(Conv2D(filters=16, kernel_size=(3, 3), padding="same", activation='relu'))
        self.model.add(Conv2D(filters=32, kernel_size=(3, 3), padding="same", activation='relu'))
        self.model.add(Permute((2, 1, 3)))
        v = self.model.layers[-1]
        self.model.add(Reshape((-1, self.height*v.output.shape[-1])))
        self.model.add(LSTM(128, return_sequences=True))
        self.model.add(Dropout(0.2))
        self.model.add(Dense(1+len(self.alphabet)))
        self.model.compile(optimizer="adam")

        self.translate_width = lambda q: q

    def to_label(self, word: str):
        return [self.alphabet_map[c] for c in word]

    def to_word(self, label):
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

