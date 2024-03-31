import string

import tensorflow as tf
from tensorflow.keras.layers import Input, Conv2D, GlobalAveragePooling2D, MaxPooling2D, Reshape, LSTM, Dense, Dropout, Flatten
import numpy as np


def main():
    alphabet = string.ascii_letters+string.digits+string.punctuation

    h, w = 28, None
    filters = 32
    kernel_size = 3
    pool_size = 2
    model = tf.keras.models.Sequential([
        Input((h, w, 1)),
        Conv2D(filters=filters, kernel_size=(kernel_size, kernel_size), activation='relu'),
        MaxPooling2D(pool_size=(pool_size, pool_size)),
        Reshape((-1, filters*(h-kernel_size+1) // pool_size)),
        LSTM(128, return_sequences=True),
        Dense(1+len(alphabet), activation="softmax")  # the 1 is the blank symbol
    ])

    image = np.ones((28, 15))
    image = image.reshape((1, 28, 15, 1))
    prediction = model.predict(image)

    input_length = np.ones(prediction.shape[0]) * prediction.shape[1]
    decoded, _ = tf.nn.ctc_greedy_decoder(
        inputs=tf.transpose(prediction, [1, 0, 2]),
        sequence_length=input_length,
        merge_repeated=True,
        blank_index=0
    )

    # To extract the decoded sequence
    decoded_classes = tf.sparse.to_dense(decoded[0], default_value=-1).numpy()

    text = "".join([alphabet[i-1] for i in decoded_classes[0]])
    print(text)


if __name__ == "__main__":
    main()
