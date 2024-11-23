#!/bin/bash
DIR=$(dirname ${BASH_SOURCE[0]})
cd $DIR/..

CONFIG_FILE="$1"

if [ "$CONFIG_FILE" == "" ]; then
  echo "CONFIG_FILE is not set"
  exit 1
fi
config=$(jq -cM . $CONFIG_FILE)
export VAULT_ADDR=$(echo $config | jq -r .vault.VAULT_ADDR)
export VAULT_TOKEN=$(echo $config | jq -r .vault.VAULT_TOKEN)
export VAULT_CACERT=""
config=$(vault kv get kv/env/$(vault token lookup | jq -r .data.meta.env) | jq .data.data)

if [ "$config" == "" ]; then
  echo "$CONFIG_FILE is empty"
  exit 2
fi

namespace=$(echo "$config" | jq -r .k8s.namespace)
domain=$(echo "$config" | jq -r .webserver.domain[0])
docker_prefix=$(echo "$config" | jq -r .k8s.docker_prefix)

for v in $namespace $domain $docker_prefix; do
  if [ "$v" == "" ] || [ "$v" == "null" ]; then
    echo "config does not define all parameters"
    exit 1
  fi
done

LABEL="$namespace"
if [ "$LABEL" == "" ]; then
  LABEL="latest"
fi

TAG=$(git describe --tags --dirty --always)

#pushd website && npm run build && popd || exit 1
docker build -f script/Dockerfile_website -t hybridocr_website:$TAG . || exit 1
docker tag hybridocr_website:$TAG ${docker_prefix}hybridocr_website:$TAG || exit 1
docker tag hybridocr_website:$TAG hybridocr_website:$LABEL || exit 1
docker tag hybridocr_website:$TAG ${docker_prefix}hybridocr_website:$LABEL || exit 1
echo
# docker image ls | grep hybridocr_website | awk '{ print $3 }' | xargs -l docker rmi -f
echo "# gcloud container images delete ${docker_prefix}hybridocr_website:$TAG"
echo docker push ${docker_prefix}hybridocr_website:$TAG
