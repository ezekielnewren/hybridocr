#!/bin/bash

if [ "$HYBRIDOCR_CONFIG_FILE" == "" ]; then
  echo "HYBRIDOCR_CONFIG_FILE is not set"
  exit 1
fi
config=$(jq -cM . $HYBRIDOCR_CONFIG_FILE)

if [ "$config" == "" ]; then
  echo "$HYBRIDOCR_CONFIG_FILE is empty"
  exit 2
fi

LABEL="$1"
if [ "$LABEL" == "" ]; then
  LABEL="latest"
fi

docker_prefix=$(echo "$config" | jq -r .docker_prefix)
TAG=$(git describe --tags --dirty --always)

pushd website && npm run build && popd || exit 1
docker build -f Dockerfile_website -t hybridocr_website:$TAG . || exit 1
docker tag hybridocr_website:$TAG ${docker_prefix}hybridocr_website:$TAG || exit 1
docker tag hybridocr_website:$TAG ${docker_prefix}hybridocr_website:$LABEL || exit 1
echo
echo "# gcloud container images delete ${docker_prefix}hybridocr_website:$TAG"
echo docker push ${docker_prefix}hybridocr_website:$TAG
