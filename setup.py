#!/usr/bin/env python
# coding=utf-8
from distutils.core import setup
from codecs import open

# files = ["README", "LICENCE"]

long_description = open("README", "r", "utf-8").read().encode("utf-8")

setup(
    name='permset',
    version='0.18',
    # http://docs.python.org/2/distutils/setupscript.html#installing-additional-files
    packages = ["permset"],
    description = "Simple utility to manage \*nix permissions on file and directory trees based on patterns.",
    author = "Robert Lujo",
    author_email = "trebor74hr@gmail.com",
    url = "https://github.com/trebor74hr/permset",
    #'permset' should be in the root.
    # TODO: 
    scripts = ["scripts/permset"],
    long_description = long_description,
    # This next part it for the Cheese Shop
    # http://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: System Administrators',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: MacOS',
        'Operating System :: POSIX',
        'Operating System :: POSIX :: Linux',
        'Operating System :: Unix',
        'Programming Language :: Python',
        'Topic :: Utilities',
        'Topic :: System :: Systems Administration',
        'Topic :: System :: Systems Administration :: Authentication/Directory',
        'Topic :: System :: System Shells',
        'Topic :: System :: Shells',
        'Topic :: Software Development',
        'Topic :: System :: Software Distribution',
      ]
    )


