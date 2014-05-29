#! /usr/bin/env python
# Copyright 2014 Peter Williams <peter@newton.cx> and collaborators.
# Licensed under the MIT License.

# I don't use the ez_setup module because it causes us to automatically build
# and install a new setuptools module, which I'm not interested in doing.

from setuptools import setup

setup (
    name = 'omegaplot',
    version = '0.2',

    zip_safe = True,
    packages = ['omega', 'oputil'],

    # install_requires = ['docutils >= 0.3'],

    # entry_points = {
    #     'console_scripts': ['bib = bibtools.cli:driver'],
    # },

    author = 'Peter Williams',
    author_email = 'peter@newton.cx',
    description = 'The last plotting package you\'ll ever need.',
    license = 'GPLv3',
    keywords = 'astronomy science',
    url = 'https://github.com/pkgw/omegaplot/',

    long_description = \
    '''This is a Cairo-based plotting package. It's got a ton of great features,
    but it's also totally undocumented. ''',

    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Topic :: Scientific/Engineering :: Astronomy',
    ],
)
