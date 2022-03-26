import copy
import os
import kopf
import kubernetes
from prodict import Prodict


SYNC_LABEL = 'synator/sync'
INCLUDE_NAMESPACES_ANNOTATION = 'synator/include-namespaces'
EXCLUDE_NAMESPACES_ANNOTATION = 'synator/exclude-namespaces'
INCLUDE_LABELS_ANNOTATION = 'synator/include-labels'
EXCLUDE_LABELS_ANNOTATION = 'synator/exclude-labels'
INCLUDE_ANNOTATIONS_ANNOTATION = 'synator/include-annotations'
EXCLUDE_ANNOTATIONS_ANNOTATION = 'synator/exclude-annotations'
DEFAULT_EXCLUDE = 'synator/'


watched_namespaces = os.getenv('WATCHED_NAMESPACES', "")
watched_namespaces = watched_namespaces.split(',') if watched_namespaces else []

kubernetes.config.load_config()
api = kubernetes.client.CoreV1Api()


@kopf.on.startup()
def handle_startup(logger, **_):
    if watched_namespaces:
        logger.info(f"Watching namespaces: {watched_namespaces or 'ALL'}")


def _is_watched_namespace(namespace, **_):
    if not watched_namespaces or namespace in watched_namespaces:
        return True
    return False


@kopf.on.create('', 'v1', 'secrets', labels={SYNC_LABEL: 'yes'}, when=_is_watched_namespace)
@kopf.on.update('', 'v1', 'secrets', labels={SYNC_LABEL: 'yes'}, when=_is_watched_namespace)
@kopf.on.create('', 'v1', 'configmaps', labels={SYNC_LABEL: 'yes'}, when=_is_watched_namespace)
@kopf.on.update('', 'v1', 'configmaps', labels={SYNC_LABEL: 'yes'}, when=_is_watched_namespace)
def handle_create_or_update(resource, new, name, namespace, annotations, logger, **_):
    target_namespaces = _get_target_namespaces(annotations, namespace)

    obj = _to_obj(new)
    _clean(obj.metadata)
    for target_namespace in target_namespaces:
        _create_or_update(resource.kind, obj, name, target_namespace, logger)


@kopf.on.delete('', 'v1', 'secrets', labels={SYNC_LABEL: 'yes'}, when=_is_watched_namespace)
@kopf.on.delete('', 'v1', 'configmaps', labels={SYNC_LABEL: 'yes'}, when=_is_watched_namespace)
def handle_delete(resource, name, namespace, annotations, logger, **_):
    target_namespaces = _get_target_namespaces(annotations, namespace)

    for target_namespace in target_namespaces:
        _delete(resource.kind, name, target_namespace, logger)


@kopf.on.create('', 'v1', 'namespaces')
def handle_create_namespace(name, logger, **_):
    api_response = api.list_secret_for_all_namespaces(label_selector=f'{SYNC_LABEL}==yes')
    for secret in api_response.items:
        new_secret = _copy(secret)
        _clean(new_secret.metadata)
        for target_namespace in _filter_target_namespaces(secret.metadata.annotations, [name]):
            _create_or_update('Secret', new_secret, secret.metadata.name, target_namespace, logger)

    api_response = api.list_config_map_for_all_namespaces(label_selector=f'{SYNC_LABEL}==yes')
    for configmap in api_response.items:
        new_configmap = _copy(configmap)
        _clean(new_configmap.metadata)
        for target_namespace in _filter_target_namespaces(configmap.metadata.annotations, [name]):
            _create_or_update('ConfigMap', new_configmap, configmap.metadata.name, target_namespace, logger)


def _copy(obj):
    d = obj.to_dict()
    # Remove "non-essential" (system) fields
    d = kopf.AnnotationsDiffBaseStorage().build(body=kopf.Body(d))
    return _to_obj(d)


def _to_obj(d: dict):
    """
    This method exists because the Kubernetes API does not allow making an object out of a dictionary
    with sensible default values.
    """

    d = copy.deepcopy(d)

    # Restore essential fields
    if 'metadata' not in d:
        d['metadata'] = {}
    if 'labels' not in d['metadata']:
        d['metadata']['labels'] = {}
    if 'annotations' not in d['metadata']:
        d['metadata']['annotations'] = {}

    return Prodict.from_dict(d)


def _clean(metadata):
    label_includes = metadata.annotations.get(INCLUDE_LABELS_ANNOTATION)
    label_excludes = (metadata.annotations.get(EXCLUDE_LABELS_ANNOTATION) or "") + f',{DEFAULT_EXCLUDE}'
    metadata.labels = _filter(label_includes, label_excludes, metadata.labels, exact=False)

    annotation_includes = metadata.annotations.get(INCLUDE_ANNOTATIONS_ANNOTATION)
    annotation_excludes = (metadata.annotations.get(EXCLUDE_ANNOTATIONS_ANNOTATION) or "") + f',{DEFAULT_EXCLUDE}'
    metadata.annotations = _filter(annotation_includes, annotation_excludes, metadata.annotations, exact=False)


def _set_metadata(obj, name, namespace):
    obj.metadata.name = name
    obj.metadata.namespace = namespace
    obj.metadata.labels['app.kubernetes.io/managed-by'] = 'synator'


def _get_target_namespaces(source_annotations, source_namespace):
    namespace_response = api.list_namespace()
    all_namespaces = [nsa.metadata.name for nsa in namespace_response.items]
    all_namespaces.remove(source_namespace)
    return _filter_target_namespaces(source_annotations, all_namespaces)


def _filter_target_namespaces(source_annotations, candidate_namespaces):
    return _filter(source_annotations.get(INCLUDE_NAMESPACES_ANNOTATION),
                   source_annotations.get(EXCLUDE_NAMESPACES_ANNOTATION),
                   candidate_namespaces)


def _filter(includes, excludes, candidates, exact=True):
    if includes:
        includes = includes.replace(' ', '').split(',')
        includes = [i for i in includes if i]  # remove blank
    if excludes:
        excludes = excludes.replace(' ', '').split(',')
        excludes = [i for i in excludes if i]  # remove blank

    filtered = candidates.copy()
    for item in filtered.copy():
        if (includes and not any(pattern == item if exact else item.startswith(pattern) for pattern in includes)) \
                or (excludes and any(pattern == item if exact else item.startswith(pattern) for pattern in excludes)):
            if isinstance(filtered, list):
                filtered.remove(item)
            else:
                del filtered[item]

    return filtered


def _create_or_update(kind, obj, name, namespace, logger):
    try:
        if kind == 'ConfigMap': api.read_namespaced_config_map(name, namespace)
        elif kind == 'Secret':  api.read_namespaced_secret(name, namespace)
        exists = True
    except kubernetes.client.ApiException:
        exists = False

    try:
        _set_metadata(obj, name, namespace)
        if not exists:
            if kind == 'ConfigMap': api.create_namespaced_config_map(namespace, obj)
            elif kind == 'Secret':  api.create_namespaced_secret(namespace, obj)
        else:
            if kind == 'ConfigMap': api.patch_namespaced_config_map(name, namespace, obj)
            elif kind == 'Secret':  api.patch_namespaced_secret(name, namespace, obj)
    except kubernetes.client.ApiException as e:
        logger.error(f"Could not create or update {kind} {namespace}/{name}", e)


def _delete(kind, name, namespace, logger):
    try:
        if kind == 'ConfigMap': obj = api.read_namespaced_config_map(name, namespace)
        elif kind == 'Secret':  obj = api.read_namespaced_secret(name, namespace)
    except kubernetes.client.ApiException:
        return

    if obj.metadata.labels and obj.metadata.labels['app.kubernetes.io/managed-by'] == 'synator':
        try:
            if kind == 'ConfigMap': api.delete_namespaced_config_map(name, namespace)
            elif kind == 'Secret':  api.delete_namespaced_secret(name, namespace)
        except kubernetes.client.ApiException as e:
            logger.error(f"Could not delete {kind} {namespace}/{name}", e)
    else:
        logger.info(f"Not deleting {kind} {namespace}/{name} because label 'app.kubernetes.io/managed-by=synator' is missing")
