import os
import sys

from distutils.core import setup

import rash

PY3 = (sys.version_info[0] >= 3)

install_requires = [
    'argparse',
]
if not PY3:
    install_requires.extend([
        'parsedatetime',
        'watchdog',
    ])


setup(
    name='rash',
    version=rash.__version__,
    packages=['rash', 'rash.utils',
              'rash.tests', 'rash.utils.tests', 'rash.functional_tests'],
    package_data={
        # See also ./MANIFEST.in
        'rash': [
            'schema.sql',
            os.path.join('ext', '*sh'),
        ],
    },
    author=rash.__author__,
    author_email='aka.tkf@gmail.com',
    url='https://github.com/tkf/rash',
    license=rash.__license__,
    description='Rash Advances Shell History',
    long_description=rash.__doc__,
    keywords='history, shell, search',
    classifiers=[
        "Development Status :: 3 - Alpha",
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.2",
        "Programming Language :: Unix Shell",
        "Topic :: System :: Shells",
        "Topic :: System :: Logging"
        # see: http://pypi.python.org/pypi?%3Aaction=list_classifiers
    ],
    install_requires=install_requires,
    entry_points={
        'console_scripts': ['rash = rash.cli:main'],
    },
)
