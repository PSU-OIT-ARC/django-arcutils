from fnmatch import fnmatch

from django.contrib.staticfiles.storage import staticfiles_storage


def load_manifest(*paths):
    """Get manifest for static files.

    .. note:: This is experimental; use with caution.

    This is for use with Django's ``ManifestStaticFilesStorage``. Its
    main purpose is to provide a way to pass the static files manifest
    to JavaScript so that static paths can be generated correctly.

    The :func:`aructils.templatetags.arc.staticfiles_manifest` template
    tag wraps this function and can be used to inject the manifest into
    an entry point template as JSON.

    Args:
        paths: If no paths are passed, the entire manifest will be
            returned. If one or more paths or passed, the manifest will
            be filtered to include only those paths; these paths can be
            shell-style patterns with wildcards (e.g., 'path/*').

    Returns:
        dict: { path => manifest path }
        None: If ``ManifestStaticFilesStorage`` if isn't being used

    """
    try:
        staticfiles_storage.load_manifest
    except AttributeError:
        return None
    else:
        manifest = staticfiles_storage.load_manifest()

    if paths:
        paths_to_remove = []
        for manifest_path in manifest:
            for path in paths:
                if not fnmatch(manifest_path, path):
                    paths_to_remove.append(manifest_path)
        for manifest_path in paths_to_remove:
            del manifest[manifest_path]

    return manifest
