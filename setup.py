#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

import nacho


REQUIREMENTS = [i.strip() for i in open("requirements.txt").readlines()]



setup(name='nacho',
    version=nacho.__version__,
    description=nacho.__description__,
    long_description=nacho.__description__,
    author=nacho.__author__,
    license=nacho.__license__,
    packages=find_packages(exclude=('doc', 'docs', 'example')),
    package_dir={'nacho': 'nacho'},
    dependency_links=[
        'https://code.google.com/p/tulip/#egg=tulip'
    ],
    install_requires=REQUIREMENTS,
    #scripts=['nacho/bin/nacho'],
    include_package_data=True)
