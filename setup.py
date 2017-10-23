#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from setuptools import setup

setup(
    name="sqli",
    version="0.1",
    description="Simple SQL injection checker",
    author="Ilja Everilä",
    author_email="saarni@gmail.com",
    url="https://github.com/everilae/sqli",
    packages=["sqli"],
    install_requires=[
        "astunparse",
        "requests",
        "beautifulsoup4",
    ],
    setup_requires=["pytest-runner"],
    tests_require=["pytest"],
    scripts=["scripts/so-checker.py"],
)
