**This is a rewritten fork of TheYkk/synator.**

It's better, cleaner, faster, but note that the API has changed.
For example, `synator/sync` is a label, not an annotation (this is important for performance). 


# Synator Kubernetes Secret and ConfigMap synchronizer

Sometimes we want to use the same ConfigMaps and Secrets in many namespaces.
Synator is a controller which automates the copying and synchronization of secrets and config across namespaces.

Synator uses [kopf](https://github.com/nolar/kopf) python framework.

[**OUTDATED** Medium writeup](https://itnext.io/kubernetes-secret-and-configmap-sync-6c6b9f906b0d)


## Installation

**NOTE: This branch is not publicly deployed. You must build the image yourself and specify it in `deploy.yml`.
See the 'Build and Deploy' section.**

Apply [deploy.yml](deploy.yml) to Kubernetes.


## Usage

Add label `synator/sync=yes` to Secret or ConfigMap.

```yaml
apiVersion: v1
kind: Secret
type: Opaque
metadata:
  name: example
  label:
    synator/sync: 'yes'
data:
  tt: dHQONTExMjMONTU=
```

### Specifying destination namespaces

Optionally add one of these annotations to include or exclude specific destination
namespaces from the sync.

Copy secret only to some namespaces:
`synator/include-namespaces='namespace1,namespace2'`

Exclude particular namespaces:
`synator/exclude-namespaces='kube-system,kube-node-lease'`

```yaml
apiVersion: v1
kind: Secret
type: Opaque
metadata:
  name: example
  labels:
    synator/sync: 'yes'
  annotations:
    synator/include-namespaces: my-fancy-namespace,my-app
data:
  tt: dHOONTExMiMONTU=
```

### Copying metadata

When creating a copy of a Secret or ConfigMap, the only metadata that is preserved is labels and annotations excluding
"system" annotations such as `last-applied-configuration`, those related to kopf, as well as prefixed with `synator/`.

Optionally, the copied labels and annotations can be further restricted.

Include *only* specific label or annotation *prefixes*:
```yaml
metadata:
  annotations:
    synator/include-labels: app.kubernetes.io/
    synator/include-annotations: cert-manager.io/
```

Exclude specific *prefixes*:
```yaml
metadata:
  annotations:
    synator/exclude-labels: app.kubernetes.io/instance
    synator/exclude-annotations: cert-manager.io/issuer
```

Include and exclude filters can be used together, and are applied in that order.

The label `app.kubernetes.io/managed-by=synator` is always set.


## Lifecycle

Object creation or update is triggered when:
 - synator is started (it looks for objects without the `kopf.zalando.org/last-handled-configuration` annotation)
 - ConfigMap or Secret is created
 - ConfigMap or Secret is labelled with `synator/sync='yes'`
 - ConfigMap or Secret is updated (its essential fields differ from those stored in `kopf.zalando.org/last-handled-configuration`)
 - A Namespace is created
 
Object update is **not** triggered when:
 - A child object does not have the label `app.kubernetes.io/managed-by=synator`

Object deletion is triggered when:
 - The parent object is deleted

Objection deletion is **not** triggered when:
 - The parent object's `synator/sync='yes'` label is removed
 - The parent object whose `synator/sync='yes'` label has been removed is deleted
 - A child object has had its `app.kubernetes.io/managed-by=synator` label removed


## Watching Namespaces

Synator is usually installed with cluster-wide permissions and watches all namespaces.
The namespaces can be restricted either through [`kopf` configuration](https://kopf.readthedocs.io/en/stable/scopes/)
or by setting the `WATCHED_NAMESPACES` environment variable.
`WATCHED_NAMESPACES` restricts the *source* namespaces, while `kopf --namespaces` restricts both source and target namespaces.
To configure either, edit [deploy.yml](deploy.yml).

- `WATCHED_NAMESPACES=""` will watch for resources across the entire cluster.
- `WATCHED_NAMESPACES="foo,bar"` will watch for resources in the foo and bar namespace.


## Build and deploy

Build docker image

```shell
docker build -t <repository>/synator:<tag> .
```

Upload docker image

```shell
docker push <repository>/synator:<tag> .
```

Edit [deploy.yml](deploy.yml) with your image path

Apply [deploy.yml](deploy.yml)

```shell
kubectl apply -f deploy.yml
```
