import os
import platform


def get_config_directory(appname):
    """
    Get OS-specific configuration directory.

    :type appname: str
    :arg  appname: capitalized name of the application

    """
    if platform.system().lower() == 'windows':
        path = os.path.join(os.getenv('APPDATA') or '~', appname, appname)
    elif platform.system().lower() == 'darwin':
        path = os.path.join('~', 'Library', 'Application Support', appname)
    else:
        path = os.path.join(os.getenv('XDG_CONFIG_HOME') or '~/.config',
                            appname.lower())
    return os.path.expanduser(path)
