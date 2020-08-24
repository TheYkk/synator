# Synator Kubernetes Secret and ConfigMap synchronizer

Synator synchronize your Secrets and ConfigMaps with your desired namespaces

# Usage
Add annotation `synator/sync=yes` to Secret or ConfigMap. 
Optionally add one of these annotations in include specific destination
namespaces, or exclude the namespaces from the sync.
`synator/include-namespaces='namespace1,namespace2'`
`synator/exclude-namespaces='kube-system,kube-node-lease'`

# Triggers
 - When update config or secret
 - When create config or secret
 
# Build and deploy
Build docker image

```
docker build -t <usename>/synator:v1 .
```

Edit deploy.yml with your image name

```
kubectl apply -f deploy.yml
```
