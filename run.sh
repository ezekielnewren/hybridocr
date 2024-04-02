#!/bin/bash

docker build -t tf-persistent .

options="--rm"
options="--restart always -d"
docker run --name tf $options --gpus all -it -v $HOME/persistent:/persistent tf-persistent
