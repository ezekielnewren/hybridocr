#!/bin/bash

docker build -f Dockerfile_backend -t hybridocr_backend .
VERSION=$(git describe --tags --abbrev=0)
docker tag hybridocr_backend:latest docker.ezekielnewren.com/hybridocr_backend:$VERSION
