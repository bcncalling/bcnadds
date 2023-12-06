from .TgGraph import TgGrpahApi


def file_upload(f):
    """Deprecated, use TgGraph.file_upload"""
    import warnings
    warnings.warn(
        "tgraph.file_upload is deprecated, use Telegraph.upload_file",
        DeprecationWarning
    )

    r = TgGraphApi().file_upload(f)
    return [i['src'] for i in r]
