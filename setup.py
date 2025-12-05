#!/usr/bin/env python
# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import print_function
from glob import glob
from os.path import join as pjoin
import os
import io
HERE = os.path.abspath(os.path.dirname(__file__))

def find_packages(top=HERE):
    """
    Find all of the packages.
    """
    packages = []
    for d, dirs, _ in os.walk(top, followlinks=True):
        if os.path.exists(pjoin(d, '__init__.py')):
            packages.append(os.path.relpath(d, top).replace(os.path.sep, '.'))
        elif d != top:
            # Don't look for packages in subfolders if current isn't a package.
            dirs[:] = []
    return packages

def get_version(file, name='__version__'):
    """Get the version of the package from the given file by
    executing it and extracting the given `name`.
    """
    path = os.path.realpath(file)
    version_ns = {}
    with io.open(path, encoding="utf8") as f:
        exec(f.read(), {}, version_ns)
    return version_ns[name]


from setuptools import setup


# The name of the project
name = 'nanohub-uidl'

# Ensure a valid python version ### deprecated
#ensure_python('>=3.3')

# Get our version
version = get_version(pjoin('nanohubuidl', '_version.py'))

long_description = ""
with open("README.md", "r") as fh:
    long_description = fh.read()

setup_args = {
    'name'            : name,
    'description'     : 'A set of tools to run create Javascript Apps, using Teleporthq UIDL schema',
    'long_description_content_type' : 'text/markdown',
    'long_description':long_description,
    'version'         : version,
    'scripts'         : glob(pjoin('scripts', '*')),
    'packages'        : find_packages(),
    'data_files'      : [
        ('assets', []),
        (
            'etc/jupyter/jupyter_notebook_config.d',
            ['nanohubuidl/jupyter-config/jupyter_server_config.d/nanohubuidl.json']
        )
    ],
    'author'          : 'Nanohub',
    'author_email'    : 'denphi@denphi.com',
    'url'             : 'https://github.com/denphi/nanohub-uidl',
    'license'         : 'BSD',
    'platforms'       : "Linux, Mac OS X, Windows",
    'keywords'        : ['IPython'],
    'classifiers'     : [
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Framework :: Jupyter',
    ],
    'include_package_data' : True,
    'install_requires' : [
        'nanohub-remote>=0.1.0',
        'simtool',
        'jupyter_server',
        'notebook>=7',
        'ipywidgets>=8.0.0,<9'
    ],
    'extras_require' : {
        'test': [
        ],
        'examples': [
        ],
        'docs': [
        ],
    },
    'entry_points' : {
        'console_scripts': [
            'run_uidl = nanohubuidl:main'
        ],
    },
}

if __name__ == '__main__':
    setup(**setup_args)
