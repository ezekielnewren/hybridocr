#!/bin/bash

config=$(jq -cM . $HYBRIDOCR_CONFIG_FILE)

if [ "$config" == "" ]; then
  echo "HYBRIDOCR_CONFIG_FILE is empty or file does not exist"
  exit 1
fi

docker_prefix=$(echo "$config" | jq -r .docker_prefix)
VERSION=$(git describe --tags --abbrev=0)

cd website && npm run build
docker build -f Dockerfile_website -t hybridocr_website:$VERSION .
docker tag hybridocr_website:$VERSION $docker_prefix/hybridocr_website:$VERSION
echo
echo docker push $docker_prefix/hybridocr_website:$VERSION
