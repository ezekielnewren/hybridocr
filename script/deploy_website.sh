#!/bin/bash
DIR=$(dirname ${BASH_SOURCE[0]})
cd $DIR

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

kubectl create namespace $namespace 2>/dev/null
kubectl -n $namespace get secret config-$namespace > /dev/null 2>&1; ec=$?
if [ $ec -eq 0 ]; then
  kubectl -n $namespace delete secret config-$namespace
  sleep 1
fi
kubectl -n $namespace create secret generic config-$namespace --from-file=config.json=$CONFIG_FILE
helm upgrade --install hw-$namespace ../helm --namespace $namespace --set domain=$domain --set docker_prefix=${docker_prefix}
