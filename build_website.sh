#!/bin/bash

config=$(jq -cM . $HYBRIDOCR_CONFIG_FILE)

if [ "$config" == "" ]; then
  echo "HYBRIDOCR_CONFIG_FILE is empty or file does not exist"
  exit 1
fi

docker_prefix=$(echo "$config" | jq -r .docker_prefix)
TAG=$(git describe --tags --dirty --always)

cd website && npm run build
docker build -f Dockerfile_website -t hybridocr_website:$TAG .
docker tag hybridocr_website:$TAG $docker_prefix/hybridocr_website:$TAG
echo
echo docker push $docker_prefix/hybridocr_website:$TAG
