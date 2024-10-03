#!/bin/bash
DIR=$(dirname ${BASH_SOURCE[0]})
cd $DIR

CONFIG_FILE="$1"

if [ "$CONFIG_FILE" == "" ]; then
  echo "CONFIG_FILE is not set"
  exit 1
fi
config=$(jq -cM . $CONFIG_FILE)

if [ "$config" == "" ]; then
  echo "$CONFIG_FILE is empty"
  exit 2
fi

namespace=$(echo $CONFIG | jq -r .k8s.namespace)
domain=$(echo $CONFIG | jq -r .express.domain[0])
docker_prefix=$(echo $CONFIG | jq -r .k8s.docker_prefix)

LABEL="$namespace"
if [ "$LABEL" == "" ]; then
  LABEL="latest"
fi

TAG=$(git describe --tags --dirty --always)

pushd website && npm run build && popd || exit 1
docker build -f Dockerfile_website -t hybridocr_website:$TAG . || exit 1
docker tag hybridocr_website:$TAG ${docker_prefix}hybridocr_website:$TAG || exit 1
docker tag hybridocr_website:$TAG ${docker_prefix}hybridocr_website:$LABEL || exit 1
echo
echo "# gcloud container images delete ${docker_prefix}hybridocr_website:$TAG"
echo docker push ${docker_prefix}hybridocr_website:$TAG
