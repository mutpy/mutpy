# -*- coding: utf-8 -*-

import sys
from setuptools import setup

if sys.hexversion < 0x3020000:
    print('MutPy requires Python 3.2 or newer!')
    sys.exit()

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name='MutPy',
    version='0.4.0',
    description='Mutation testing tool for Python 3.x source code.',
    author='Konrad Hałas',
    author_email='halas.konrad@gmail.com',
    url='https://github.com/mutpy/mutpy',
    download_url='https://github.com/mutpy/mutpy',
    packages=['mutpy'],
    scripts=['bin/mut.py'],
    install_requires=requirements,
    test_suite='mutpy.test',
    classifiers=[
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Testing',
        'License :: OSI Approved :: Apache Software License',
    ],
)
