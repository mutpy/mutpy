# -*- coding: utf-8 -*-

import sys
from setuptools import setup

if sys.hexversion < 0x3020000:
    print('MutPy requires Python 3.2 or newer!')
    sys.exit()

setup(
    name='MutPy',
    version='0.3.2',
    description='Mutation testing tool for Python 3.x source code.',
    author='Konrad Hałas',
    author_email='halas.konrad@gmail.com',
    url='https://bitbucket.org/khalas/mutpy',
    download_url='https://bitbucket.org/khalas/mutpy',
    packages=['mutpy'],
    scripts=['bin/mut.py'],
    install_requires=['PyYAML>=3.1'],
    test_suite='mutpy.test',
    classifiers=[
        'Programming Language :: Python :: 3.2',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Testing',
        'License :: OSI Approved :: Apache Software License',
    ],
)
