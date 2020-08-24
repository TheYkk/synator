import kopf
import kubernetes


@kopf.on.create('', 'v1', 'secrets', labels={'synator/sync': 'yes'})
@kopf.on.update('', 'v1', 'secrets', labels={'synator/sync': 'yes'})
def updateSecret(body, meta, spec, status, old, new, diff, **kwargs):
    print("SYNC SECRET ", meta.name)
    api = kubernetes.client.CoreV1Api()
    namespace_response = api.list_namespace()
    namespaces = [nsa.metadata.name for nsa in namespace_response.items]
    namespaces.remove('kube-public')
    namespaces.remove('kube-node-lease')
    namespaces.remove(meta.namespace)

    secret = api.read_namespaced_secret(meta.name, meta.namespace)
    secret.metadata.labels.pop('synator/sync')
    secret.metadata.resource_version = None
    for ns in namespaces:
        secret.metadata.namespace = ns
        api.create_namespaced_secret(
            ns, secret
        )


@kopf.on.create('', 'v1', 'configmaps', labels={'synator/sync': 'yes'})
@kopf.on.update('', 'v1', 'configmaps', labels={'synator/sync': 'yes'})
def updateConfigMap(body, meta, spec, status, old, new, diff, **kwargs):
    print("SYNC CFG ", meta.name)
    api = kubernetes.client.CoreV1Api()
    namespace_response = api.list_namespace()
    namespaces = [nsa.metadata.name for nsa in namespace_response.items]
    namespaces.remove('kube-public')
    namespaces.remove('kube-node-lease')
    namespaces.remove(meta.namespace)

    cfg = api.read_namespaced_config_map(meta.name, meta.namespace)
    cfg.metadata.labels.pop('synator/sync')
    cfg.metadata.resource_version = None
    for ns in namespaces:
        cfg.metadata.namespace = ns
        api.create_namespaced_config_map(
            ns, cfg
        )
