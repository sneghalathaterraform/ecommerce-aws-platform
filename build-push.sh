#!/usr/bin/env bash
set -euo pipefail
REGION=ap-south-1
TAG=${1:-v1}
ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
REGISTRY=$ACCOUNT.dkr.ecr.$REGION.amazonaws.com
docker --version
aws ecr describe-repositories --repository-names ecommerce-app --region $REGION >/dev/null 2>&1 \
  || aws ecr create-repository --repository-name ecommerce-app --region $REGION \
       --image-scanning-configuration scanOnPush=true >/dev/null
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $REGISTRY
docker build --platform linux/amd64 --build-arg APP_VERSION=$TAG -t $REGISTRY/ecommerce-app:$TAG .
docker rm -f shoptest >/dev/null 2>&1 || true
docker run -d -p 18081:8080 --name shoptest $REGISTRY/ecommerce-app:$TAG >/dev/null
sleep 5
echo "livez:  $(curl -s localhost:18081/livez)"
echo "health: $(curl -s localhost:18081/health)"
docker rm -f shoptest >/dev/null
docker push $REGISTRY/ecommerce-app:$TAG
aws ecr describe-images --repository-name ecommerce-app --region $REGION \
  --query 'imageDetails[].imageTags' --output text
echo "IMAGE: $REGISTRY/ecommerce-app:$TAG"
