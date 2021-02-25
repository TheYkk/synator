# Synator Kubernetes Secret and ConfigMap synchronizer

Sometimes we want to use secrets in different namespaces, unfortunately, we can’t do without any helper operators or manual copying because in kubernetes secrets and configmaps are namespace. We can copy secrets and configmaps when we have a couple of namespaces and secrets. But when we have dozens of namespaces, it can be very complicated. 

Synator uses [kopf](https://github.com/nolar/kopf) python framework. Its easy to use.
## Deployment
It’s easy to use synator on K8s. All we have to do is deploy [deploy.yml](https://github.com/TheYkk/synator/blob/master/deploy.yml) to Kubernetes.

## Usage
Add annotation `synator/sync=yes` to Secret or ConfigMap. 
![secret.yaml](https://miro.medium.com/max/2400/1*3gXBYpff106HREtJuWIu0Q.png)

Optionally add one of these annotations in include specific destination
namespaces, or exclude the namespaces from the sync.

For only sync in this namespaces:
`synator/include-namespaces='namespace1,namespace2'`

Sync all namespaces excludes this namespaces:
`synator/exclude-namespaces='kube-system,kube-node-lease'`

![secret.yaml](https://miro.medium.com/max/2400/1*UH4iTu3Gg6DkofHyX2KDHg.png)

## Reload pod when config upgraded
Add annotation `synator/reload: "secret:example"` to pod or deployment template
When secret example updated busybox pod will reload

Note: For multiple secrte or configmap:
`synator/reload: "secret:example,secret:example2,configmap:example..."`

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
## Triggers
 - When update config or secret
 - When create config or secret

## Watching Namespaces

synator Operator installs with cluster wide permissions, however you can optionally control which namespaces it watches by by setting the WATCH_NAMESPACE environment variable.

`WATCH_NAMESPACE` can be omitted entirely, or a comma separated list of k8s namespaces.

- `WATCH_NAMESPACE=""` will watch for resources across the entire cluster.
- `WATCH_NAMESPACE="foo"` will watch for resources in the foo namespace.
- `WATCH_NAMESPACE="foo,bar"` will watch for resources in the foo and bar namespace.

## Build and deploy
Build docker image

```
docker build -t <usename>/synator:v1 .
```

Edit deploy.yml with your image name

```
kubectl apply -f deploy.yml
```
