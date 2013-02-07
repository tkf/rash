def isearch_run():
    """
    Interactive search.

    """
    from .config import ConfigStore
    from .interactive_search import launch_isearch
    launch_isearch(ConfigStore())


def isearch_add_arguments(parser):
    pass


commands = [
    ('isearch', isearch_add_arguments, isearch_run),
]
