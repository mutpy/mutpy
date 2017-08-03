# -*- coding: utf-8 -*-

import sys

import mutpy
from setuptools import setup

if sys.hexversion < 0x3030000:
    print('MutPy requires Python 3.3 or newer!')
    sys.exit()

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

with open('README.rst') as f:
    long_description = f.read()

setup(
    name='MutPy',
    version=mutpy.__version__,
    description='Mutation testing tool for Python 3.x source code.',
    long_description=long_description,
    author='Konrad Hałas',
    author_email='halas.konrad@gmail.com',
    url='https://github.com/mutpy/mutpy',
    download_url='https://github.com/mutpy/mutpy',
    packages=['mutpy'],
    scripts=['bin/mut.py'],
    install_requires=requirements,
    test_suite='mutpy.test',
    classifiers=[
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Testing',
        'License :: OSI Approved :: Apache Software License',
    ],
)
