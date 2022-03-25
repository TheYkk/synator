import kopf
import kubernetes
import os

watched_namespaces  = os.getenv('WATCHED_NAMESPACES', "").split(',')
def is_watched_namespace(namespace, **_):
    if not watched_namespaces or namespace in watched_namespaces:
        return True
    return False


@kopf.on.create('', 'v1', 'secrets', annotations={'synator/sync': 'yes'}, when=is_watched_namespace)
@kopf.on.update('', 'v1', 'secrets', annotations={'synator/sync': 'yes'}, when=is_watched_namespace)
def handle_secret(body, meta, spec, status, old, new, diff, **kwargs):
    api = kubernetes.client.CoreV1Api()

    namespace_response = api.list_namespace()
    all_namespaces = [nsa.metadata.name for nsa in namespace_response.items]
    all_namespaces.remove(meta.namespace)
    target_namespaces = filter_target_namespaces(meta, all_namespaces)

    secret = api.read_namespaced_secret(meta.name, meta.namespace)
    secret.metadata.annotations.pop('synator/sync')
    secret.metadata.resource_version = None
    secret.metadata.uid = None

    for ns in target_namespaces:
        secret.metadata.namespace = ns
        # try to pull the Secret object then patch it, try creating it if we can't
        try:
            api.read_namespaced_secret(meta.name, ns)
            api.patch_namespaced_secret(meta.name, ns, secret)
        except kubernetes.client.rest.ApiException as e:
            print(e.args)
            api.create_namespaced_secret(ns, secret)


@kopf.on.create('', 'v1', 'configmaps', annotations={'synator/sync': 'yes'}, when=is_watched_namespace)
@kopf.on.update('', 'v1', 'configmaps', annotations={'synator/sync': 'yes'}, when=is_watched_namespace)
def handle_configMap(body, meta, spec, status, old, new, diff, **kwargs):
    api = kubernetes.client.CoreV1Api()

    namespace_response = api.list_namespace()
    all_namespaces = [nsa.metadata.name for nsa in namespace_response.items]
    all_namespaces.remove(meta.namespace)
    target_namespaces = filter_target_namespaces(meta, all_namespaces)

    cm = api.read_namespaced_config_map(meta.name, meta.namespace)
    cm.metadata.annotations.pop('synator/sync')
    cm.metadata.resource_version = None
    cm.metadata.uid = None

    for ns in target_namespaces:
        cm.metadata.namespace = ns
        # try to pull the ConfigMap object then patch it, try to create it if we can't
        try:
            api.read_namespaced_config_map(meta.name, ns)
            api.patch_namespaced_config_map(meta.name, ns, cm)
        except kubernetes.client.rest.ApiException as e:
            print(e.args)
            api.create_namespaced_config_map(ns, cm)


def filter_target_namespaces(meta, namespaces):
    target_namespaces = []
    # look for a namespace inclusion label first, if we don't find that, assume all namespaces are the target
    if 'synator/include-namespaces' in meta.annotations:
        value = meta.annotations['synator/include-namespaces']
        namespaces_to_include = value.replace(' ', '').split(',')
        for ns in namespaces_to_include:
            if ns in namespaces:
                target_namespaces.append(ns)
            else:
                print(
                    f"WARNING: include-namespaces requested I add this resource to a non-existing namespace: {ns}")
    else:
        # we didn't find a namespace inclusion label, so let's see if we were told to exclude any
        target_namespaces = namespaces
        if 'synator/exclude-namespaces' in meta.annotations:
            value = meta.annotations['synator/exclude-namespaces']
            namespaces_to_exclude = value.replace(' ', '').split(',')
            if len(namespaces_to_exclude) < 1:
                print(
                    "WARNING: exclude-namespaces was specified, but no values were parsed")

            for ns in namespaces_to_exclude:
                if ns in target_namespaces:
                    target_namespaces.remove(ns)
                else:
                    print(
                        f"WARNING: I was told to exclude namespace {ns}, but it doesn't exist on the cluster")

    return target_namespaces


@kopf.on.create('', 'v1', 'namespaces')
def handle_namespace(spec, name, meta, logger, **kwargs):
    api = kubernetes.client.CoreV1Api()

    try:
        api_response = api.list_secret_for_all_namespaces()
        # TODO: Add configmap
        for secret in api_response.items:
            # Check secret have annotation
            if secret.metadata.annotations and secret.metadata.annotations.get("synator/sync") == "yes":
                secret.metadata.annotations.pop('synator/sync')
                secret.metadata.resource_version = None
                secret.metadata.uid = None
                for ns in filter_target_namespaces(secret.metadata, [name]):
                    secret.metadata.namespace = ns
                    try:
                        api.read_namespaced_secret(
                            secret.metadata.name, ns)
                        api.patch_namespaced_secret(
                            secret.metadata.name, ns, secret)
                    except kubernetes.client.rest.ApiException as e:
                        print(e.args)
                        api.create_namespaced_secret(ns, secret)
    except kubernetes.client.rest.ApiException as e:
        print("Exception when calling CoreV1Api->list_secret_for_all_namespaces: %s\n" % e)
