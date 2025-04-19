#! /usr/bin/env python
# Copyright Peter Williams <peter@newton.cx> and collaborators.
# (This file) Licensed under the MIT License.

from setuptools import setup

setup(
    name="omegaplot",  # cranko project-name
    version="0.dev0",  # cranko project-version
    # This package actually *is* zip-safe, but I've run into issues with
    # installing it as a Zip: in particular, the install sometimes fails with
    # "bad local file header", and reloading a module after a reinstall in
    # Jupyter gives an ImportError with the same message. These are annoying
    # enough and I don't really care so we just install it as flat files.
    zip_safe=False,
    packages=["omega", "oputil"],
    install_requires=[
        "pycairo >= 1.14",
    ],
    entry_points={
        "console_scripts": [
            "omegafig = oputil.omegafig:cmdline",
            "omegamap = oputil.omegamap:cmdline",
        ],
    },
    author="Peter Williams",
    author_email="peter@newton.cx",
    description="The last plotting package you'll ever need.",
    license="GPLv3",
    keywords="astronomy science",
    url="https://github.com/pkgw/omegaplot/",
    long_description="""This is a Cairo-based plotting package. It's got a ton of great features,
    but it's also totally undocumented. """,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Topic :: Scientific/Engineering :: Astronomy",
    ],
)
