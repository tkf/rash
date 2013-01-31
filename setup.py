import os

from distutils.core import setup

import rash

setup(
    name='rash',
    version=rash.__version__,
    packages=['rash', 'rash.utils', 'rash.tests'],
    package_data={
        'rash': [os.path.join('ext', '*sh')],
    },
    author=rash.__author__,
    author_email='aka.tkf@gmail.com',
    url='https://github.com/tkf/rash',
    license=rash.__license__,
    description='Rash Advances Shell History',
    long_description=rash.__doc__,
    keywords='history, shell',
    classifiers=[
        "Development Status :: 3 - Alpha",
        # see: http://pypi.python.org/pypi?%3Aaction=list_classifiers
    ],
    install_requires=[
        'argparse',
    ],
    entry_points={
        'console_scripts': ['rash = rash.cli:main'],
    },
)
