#!/usr/bin/env python

import ez_setup
ez_setup.use_setuptools()
from setuptools import setup, find_packages

setup(
    name='Albo',
    version='0.1',
    description='Automatic lesion to brain region overlap computation',

    packages=find_packages(),
    entry_points={
        'console_scripts': ['albo = albo:main']
    },

    install_requires=[],
    package_data={'albo': ['config/*']},

    author='Lennart Weckeck',
    author_email='lennart.weckeck@student.uni-luebeck.de',
    url='https://www.github.com/lweckeck/Albo',
)
