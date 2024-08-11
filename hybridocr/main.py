import math
import os
import random
import struct
import time
import json
import sys
# from random import random

from tqdm import tqdm

from hybridocr.engine import OCREngine
from hybridocr.generate import TextToImageGenerator, TextToImageIterator
from pathlib import Path
from fontTools.ttLib import TTFont
from hybridocr.core import *

import argparse

import os
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
import tensorflow as tf


def parse_arguments(argv):
    parser = argparse.ArgumentParser(description='Process train and test file paths.')

    parser.add_argument("--hybridocr_home", type=str,
                        default=os.getenv("HYBRIDOCR_HOME", None),
                        help="directory of the hybridocr home, this can also be specified as an the envvar HYBRIDOCR_HOME")

    parser.add_argument('--train', type=str,
                        help='path to the training file relative to the home directory')

    parser.add_argument('--test', type=str,
                        help='path to the training file relative to the home directory')

    args = parser.parse_args(argv)

    if args.hybridocr_home is None:
        print("must specify hybridocr_home", file=sys.stderr)
    args.hybridocr_home = Path(args.hybridocr_home)

    return args


def go0():
    # tf.debugging.enable_check_numerics()

    args = parse_arguments(sys.argv[1:])

    if args.train is not None:
        beg = time.time()

        engine = OCREngine()

        file_train = args.hybridocr_home / args.train

        with open(file_train) as fd:
            train_config = json.loads(fd.read())

        dictionary = []

        dir_wordlist = args.hybridocr_home / "wordlist"
        for file_name in train_config["dictionary"]:
            file_dictionary = dir_wordlist / file_name
            with open(file_dictionary) as fd:
                dictionary += [v.rstrip() for v in fd.readlines()]

        generator = TextToImageGenerator(args.hybridocr_home, engine.alphabet, dictionary, train_config["font"], engine.height)
        elapsed = time.time() - beg
        print("time to initialize:", elapsed)

        count = 0
        beg = time.time()

        file_model = args.hybridocr_home/"model.keras"

        dist = split_distribution(train_config["split"], len(generator))
        dataset_range = dist[0]
        checkpoint = train_config.get("checkpoint", 0)
        sub_range = (checkpoint, dataset_range[1] - dataset_range[0])
        it = TextToImageIterator(generator, dataset_range, sub_range, train_config["batch_size"], None,
                                 engine.translate_width, engine.to_label)

        # with tqdm(initial=it.local_range[0], total=len(it)) as counter:
        #     for sample, label in it.stream():
        #         logits = engine.model(sample)
        #         loss = TextToImageIterator.loss(label, logits)
        #         counter.update(label.shape[0])
        #         loss_view = "{:.5f}".format(float(tf.reduce_mean(loss)))
        #         counter.set_postfix(loss=loss_view)
        #         pass

        strictly_cpu = os.environ.get("CUDA_VISIBLE_DEVICES")
        strictly_cpu = strictly_cpu is not None and strictly_cpu == "-1"

        random.seed(train_config["seed"])
        seed_list = [None]
        for _ in range(1, train_config["epoch"]):
            x = random.randint(0, 2**64-1)
            seed_list.append(x)

        callbacks = [TimeCheckpoint(train_config)]
        # if not strictly_cpu:
        callbacks.append(TerminateOnNaN())

        engine.model.compile(optimizer="adam", loss=TextToImageIterator.loss)
        for epoch in range(train_config["epoch"]):
            it.set_seed(seed_list[epoch])

            ds = it.dataset()
            ds.prefetch(buffer_size=tf.data.AUTOTUNE)

            engine.model.fit(x=ds, y=None, batch_size=train_config["batch_size"], epochs=1,
                             steps_per_epoch=it.batches(),
                             callbacks=callbacks
                             )
            if engine.model.terminated_on_nan:
                break
            engine.model.save(file_model)

        elapsed = time.time() - beg
        print("total time:", elapsed)
        print("rate:", float(count) / elapsed)


def go1():
    dir_home = Path(sys.argv[1])
    file_config = dir_home / "config.json"

    beg = time.time()
    with open(file_config) as fd:
        config = json.loads(fd.read())

    for v in config["font"]:
        path = dir_home / "fonts" / v

        font = TTFont(path)
        print(path.name)
        for axis in font['fvar'].axes:
            print("   ", axis.axisTag)

    pass


def main():
    go0()


if __name__ == "__main__":
    main()
