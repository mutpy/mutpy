# -*- coding: utf-8 -*-

import sys

from setuptools import setup

import mutpy

if sys.hexversion < 0x3030000:
    print('MutPy requires Python 3.3 or newer!')
    sys.exit()

with open('requirements/production.txt') as f:
    requirements = f.read().splitlines()

with open('README.rst') as f:
    long_description = f.read()

setup(
    name='MutPy',
    version=mutpy.__version__,
    python_requires='>=3.3',
    description='Mutation testing tool for Python 3.x source code.',
    long_description=long_description,
    author='Konrad Hałas',
    author_email='halas.konrad@gmail.com',
    url='https://github.com/mutpy/mutpy',
    download_url='https://github.com/mutpy/mutpy',
    packages=['mutpy', 'mutpy.operators', 'mutpy.test_runners'],
    package_data={'mutpy': ['templates/*.html']},
    scripts=['bin/mut.py'],
    install_requires=requirements,
    extras_require={
        'pytest': ["pytest>=3.0"]
    },
    test_suite='mutpy.test',
    classifiers=[
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Testing',
        'License :: OSI Approved :: Apache Software License',
    ],
)
