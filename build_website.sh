#!/bin/bash

docker build -f Dockerfile_website -t hybridocr_website .
VERSION=$(git describe --tags --abbrev=0)
docker tag hybridocr_website:latest docker.ezekielnewren.com/hybridocr_website:$VERSION
