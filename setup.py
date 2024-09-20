#!/usr/bin/env python3

from os import path

from setuptools import setup

here = path.abspath(path.dirname(__file__))

# get version
with open(path.join(here, "itu_p1203", "__init__.py")) as version_file:
    for line in version_file:
        if line.startswith("__version__"):
            version = line.split("=")[1].strip().replace('"', "")
            break

# Get the long description from the README file
with open(path.join(here, "README.md")) as f:
    long_description = f.read()

# Get the history from the CHANGES file
with open(path.join(here, "CHANGELOG.md")) as f:
    history = f.read()

setup(
    name="itu_p1203",
    version=version,
    description="ITU-T P.1203 Standalone Model",
    long_description=long_description + "\n\n" + history,
    long_description_content_type="text/markdown",
    # author="Werner Robitza",
    # author_email='werner.robitza@gmail.com',
    # url='https://example.com/',
    packages=["itu_p1203"],
    include_package_data=True,
    install_requires=["numpy"],
    package_data={"itu_p1203": ["trees/*"]},
    # license="Custom",
    zip_safe=False,
    keywords="video, p1203",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Multimedia :: Video",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
    python_requires=">=3.9",
    entry_points={"console_scripts": ["p1203-standalone = itu_p1203.__main__:main"]},
)
