#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

import nacho


setup(name='nacho',
    version=nacho.__version__,
    description=nacho.__description__,
    long_description=nacho.__description__,
    author=nacho.__author__,
    license=nacho.__license__,
    packages=find_packages(exclude=('doc', 'docs', 'example')),
    package_dir={'nacho': 'nacho'},
    #scripts=['nacho/bin/nacho'],
    include_package_data=True)
