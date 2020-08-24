# Synator Kubernetes Secret and ConfigMap synchronizer

Synator synchronize your Secrets and ConfigMaps with your all namespaces

# Usage
Add label `synator/sync=yes` to Secret or ConfigMap.

# Triggers
 - When update config or secret
 - When create config or secret
 
# Build and deeploy
Build docker image

```
docker build -t <usename>/synator:v1 .
```

Edit deploy.yml with your image name

```
kubectl apply -f deploy.yml
```