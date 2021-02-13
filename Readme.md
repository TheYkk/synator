# Synator Kubernetes Secret and ConfigMap synchronizer

Sometimes we want to use secrets in different namespaces, unfortunately, we can’t do without any helper operators or manual copying because in kubernetes secrets and configmaps are namespace. We can copy secrets and configmaps when we have a couple of namespaces and secrets. But when we have dozens of namespaces, it can be very complicated. 

# Usage
Add annotation `synator/sync=yes` to Secret or ConfigMap. 
Optionally add one of these annotations in include specific destination
namespaces, or exclude the namespaces from the sync.
`synator/include-namespaces='namespace1,namespace2'`
`synator/exclude-namespaces='kube-system,kube-node-lease'`

# Reload pod when config upgraded
Add annotation `synator/reload: "secret:example"` to pod or deployment template
When secret example updated busybox pod will reload
```
apiVersion: apps/v1
kind: Deployment
metadata:
  name: busybox
  namespace: default
spec:
  replicas: 1
  selector:
    matchLabels:
      name: busybox
  template:
    metadata:
      labels:
        name: busybox
      annotations:
        synator/reload: "secret:selam"
    spec:
      containers:
        - name: busybox
          image: busybox
          command:
            - "sleep"
            - "1h"
```
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
