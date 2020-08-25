import kopf
import kubernetes


@kopf.on.create('', 'v1', 'secrets', annotations={'synator/sync': 'yes'})
@kopf.on.update('', 'v1', 'secrets', annotations={'synator/sync': 'yes'})
def updateSecret(body, meta, spec, status, old, new, diff, **kwargs):
    api = kubernetes.client.CoreV1Api()
    namespace_response = api.list_namespace()
    namespaces = [nsa.metadata.name for nsa in namespace_response.items]
    namespaces.remove(meta.namespace)

    secret = api.read_namespaced_secret(meta.name, meta.namespace)
    secret.metadata.annotations.pop('synator/sync')
    secret.metadata.resource_version = None
    secret.metadata.uid = None
    for ns in parseTargetNamespaces(meta, namespaces):
        secret.metadata.namespace = ns
        # try to pull the Secret object then patch it, try creating it if we can't
        try:
            cm = api.read_namespaced_secret(meta.name, ns)
            api.patch_namespaced_secret(meta.name, ns, secret)
        except kubernetes.client.rest.ApiException as e:
            print(e.args)
            api.create_namespaced_secret(ns, secret)


@kopf.on.create('', 'v1', 'configmaps', annotations={'synator/sync': 'yes'})
@kopf.on.update('', 'v1', 'configmaps', annotations={'synator/sync': 'yes'})
def updateConfigMap(body, meta, spec, status, old, new, diff, **kwargs):
    # kopf.info(f"SYNC CFG {meta.name}", reason='event')
    api = kubernetes.client.CoreV1Api()
    namespace_response = api.list_namespace()
    namespaces = [nsa.metadata.name for nsa in namespace_response.items]
    namespaces.remove(meta.namespace)

    cfg = api.read_namespaced_config_map(meta.name, meta.namespace)
    cfg.metadata.annotations.pop('synator/sync')
    cfg.metadata.resource_version = None
    cfg.metadata.uid = None
    for ns in parseTargetNamespaces(meta, namespaces):
        cfg.metadata.namespace = ns
        # try to pull the ConfigMap object then patch it, try to create it if we can't
        try:
            cm = api.read_namespaced_config_map(meta.name, ns)
            api.patch_namespaced_config_map(meta.name, ns, cfg)
        except kubernetes.client.rest.ApiException as e:
            print(e.args)
            api.create_namespaced_config_map(ns, cfg)

def parseTargetNamespaces(meta, namespaces):
    namespace_list = []
    # look for a namespace inclusion label first, if we don't find that, assume all namespaces are the target
    if 'synator/include-namespaces' in meta.annotations:
        value = meta.annotations['synator/include-namespaces']
        namespaces_to_include = value.replace(' ', '').split(',')
        for ns in namespaces_to_include:
            if ns in namespaces:
                namespace_list.append(ns)
            else:
                print(f"WARNING: include-namespaces requested I add this resource to a non-existing namespace: {ns}")
    else:
        # we didn't find a namespace inclusion label, so let's see if we were told to exclude any
        namespace_list = namespaces
        if 'synator/exclude-namespaces' in meta.annotations:
            value = meta.annotations['synator/exclude-namespaces']
            namespaces_to_exclude = value.replace(' ', '').split(',')
            if len(namespaces_to_exclude) < 1:
                print("WARNING: exclude-namespaces was specified, but no values were parsed")

            for ns in namespaces_to_exclude:
                if ns in namespace_list:
                    namespace_list.remove(ns)
                else:
                    print(f"WARNING: I was told to exclude namespace {ns}, but it doesn't exist on the cluster")

    return namespace_list
