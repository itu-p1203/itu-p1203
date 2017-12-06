#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import itu_p1203
from setuptools import setup
# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Get the history from the HISTORY file
with open(path.join(here, 'HISTORY.md'), encoding='utf-8') as f:
    history = f.read()

try:
    import pypandoc
    long_description = pypandoc.convert_text(long_description, 'rst', format='md')
    history = pypandoc.convert_text(history, 'rst', format='md')
except ImportError:
    print("pypandoc module not found, could not convert Markdown to RST")

setup(
    name='p1203-standalone',
    version=itu_p1203.__version__,
    description="ITU-T P.1203 Standalone Model",
    long_description=long_description + '\n\n' + history,
    # author="Werner Robitza",
    # author_email='werner.robitza@gmail.com',
    # url='https://example.com/',
    packages=['itu_p1203'],
    include_package_data=True,
    install_requires=["numpy", "scipy", "pandas"],
    package_data={
        '': ['itu_p1203/trees/*']
    },
    # license="Custom",
    zip_safe=False,
    keywords='video, p1203',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Multimedia :: Video',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    entry_points={
        'console_scripts': [
            'p1203-standalone = itu_p1203.__main__:main'
        ]
    },
)
