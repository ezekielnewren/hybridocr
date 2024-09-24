#!/bin/bash

NAMESPACE=ingress

STATIC_IP=$(gcloud compute addresses describe ingress-ip --region us-west3 --format="get(address)")
if [ "$STATIC_IP" == "" ]; then
  echo "failed to query the static ip address"
  exit 1
fi

CLOUDFLARE_IP_RANGES=$(curl https://www.cloudflare.com/ips-v4 2>/dev/null | tr '\n' ',')
if [ "$CLOUDFLARE_IP_RANGES" == "" ]; then
  echo "failed to query the cloudflare ip ranges"
  exit 2
fi

helm install traefik traefik/traefik \
  --namespace $NAMESPACE \
  -f traefik-values.yaml \
  --set service.spec.loadBalancerIP="$STATIC_IP" \
  --set service.spec.loadBalancerSourceRanges="{$CLOUDFLARE_IP_RANGES}"

kubectl -n $NAMESPACE apply -f traefik-tlsstore.yaml
