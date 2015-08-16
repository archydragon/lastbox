#!/usr/bin/env python
from setuptools import setup, find_packages
from os import path
import sys


PWD = path.abspath(path.dirname(__file__))
with open(path.join(PWD, 'README.md')) as f:
    LONG_DESC = f.read()

import lastbox

setup(
    name = 'lastbox',
    version = lastbox.VERSION,
    description = "Last.fm submission script for Rockbox' scrobbler.log",
    long_description = LONG_DESC,
    url = 'https://github.com/Mendor/lastbox',
    author = 'Nikita K.',
    author_email = 'mendor@yuuzukiyo.net',
    license = 'MIT',
    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2 :: Only',
        'Topic :: Internet :: Log Analysis',
        'Topic :: Utilities'
    ],
    keywords = 'last.fm rockbox scrobbling',
    py_modules = ['lastbox'],
    entry_points = {
        'console_scripts': ['lastbox=lastbox:main']
    } 
)