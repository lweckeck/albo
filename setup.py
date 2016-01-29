#!/usr/bin/env python

import ez_setup
ez_setup.use_setuptools()
from setuptools import setup, find_packages

setup(
    name='Albo',
    version='0.1',
    description='Automatic lesion to brain region overlap computation',

    packages=['albo', 'albo.interfaces'],
    entry_points={
        'console_scripts': ['albo = albo:main']
    },

    install_requires=[
        'MedPy>=0.2.2',
        'nipype>=0.11.0',
        'numpy>=1.6.1',
        'scipy>=0.9',
        'scikit-learn>=0.16.1',
    ],
    package_data={'albo': ['config/*']},

    author='Lennart Weckeck',
    author_email='lennart.weckeck@student.uni-luebeck.de',
    url='https://www.github.com/lweckeck/Albo',
)
