#!/usr/bin/env python
# coding: utf-8

from setuptools import find_packages, setup

with open("README.md", "r", encoding='utf8') as fh:
    long_description = fh.read()

package_dir = {
    'missionpanel': 'missionpanel',
}

setup(
    name='missionpanel',
    version='1.4.4',
    author='yindaheng98',
    author_email='yindaheng98@gmail.com',
    url='https://github.com/yindaheng98/missionpanel',
    description=u'A mission panel',
    long_description=long_description,
    long_description_content_type="text/markdown",
    package_dir={'missionpanel': 'missionpanel'},
    packages=['missionpanel'] + ["missionpanel." + package for package in find_packages(where="missionpanel")],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        'sqlalchemy>=2',
        'chardet',
    ]
)
