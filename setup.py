#!/usr/bin/env python
# -*- coding: utf-8 -*-

import codecs
import os
import re
from setuptools import setup

root_dir = os.path.abspath(os.path.dirname(__file__))


def get_build_number():
    fname = 'build.info'
    if os.path.isfile(fname):
        with open(fname) as f:
            build_number = f.read()
            build_number = re.sub("[^a-z0-9]+","", build_number, flags=re.IGNORECASE)
            return '.' + build_number

    return ''


def get_version(package_name):
    build_number = get_build_number()

    version_re = re.compile(r"^__version__ = [\"']([\w_.-]+)[\"']$")
    package_components = package_name.split('.')
    init_path = os.path.join(root_dir, *(package_components + ['__init__.py']))
    with codecs.open(init_path, 'r', 'utf-8') as f:
        for line in f:
            match = version_re.match(line[:-1])
            if match:
                return match.groups()[0]+build_number

    return '0.1.0' + build_number

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read().replace('.. :changelog:', '')


requirements = [
    'six>=1.10.0',
    'graphene~=0.9.0'
]

test_requirements = [
    'PyYAML==3.11'
]

setup(
    name='graphene_gae',
    version=get_version('graphene_gae'),
    description="Graphene GAE Integration",
    long_description=readme + '\n\n' + history,
    author="Eran Kampf",
    author_email='eran@ekampf.com',
    url='https://github.com/ekampf/graphene_gae',
    packages=[
        'graphene_gae',
    ],
    package_dir={'graphene_gae': 'graphene_gae'},
    include_package_data=True,
    install_requires=requirements,
    license="BSD",
    zip_safe=False,
    keywords='graphene_gae',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
    ],
    test_suite='tests',
    tests_require=test_requirements
)
