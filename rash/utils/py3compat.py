import os
import sys
PY3 = (sys.version_info[0] >= 3)

try:
    getcwd = os.getcwd
except AttributeError:
    getcwd = os.getcwdu
