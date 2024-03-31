import tensorflow as tf
from tensorflow.keras.layers import Input, Conv2D, GlobalAveragePooling2D, MaxPooling2D, Reshape, LSTM, Dense, Dropout, Flatten


def main():
    h, w = 28, None
    filters = 32
    kernel_size = 3
    pool_size = 2
    model = tf.keras.models.Sequential([
        Input((h, w, 1)),
        Conv2D(filters=filters, kernel_size=(kernel_size, kernel_size), activation='relu'),
        MaxPooling2D(pool_size=(pool_size, pool_size)),
        Reshape((-1, filters*(h-kernel_size+1) // pool_size)),
        LSTM(128),
        Dense(10, activation="softmax")
    ])


if __name__ == "__main__":
    main()
