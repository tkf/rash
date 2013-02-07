def isearch_run(query):
    """
    Interactive search.

    """
    from .config import ConfigStore
    from .interactive_search import launch_isearch
    launch_isearch(ConfigStore(), query=query)


def isearch_add_arguments(parser):
    parser.add_argument(
        'query', nargs='?', default='--cwd . ',
        help='default query')


commands = [
    ('isearch', isearch_add_arguments, isearch_run),
]
