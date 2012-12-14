#!/usr/bin/env python
# coding=utf-8
from distutils.core import setup
from codecs import open

long_description = open("README.md", "r", "utf-8").read().encode("utf-8")

# NOTE: all additional files for distro is in MANIFEST.in
#       for files that need to be installed, see:
#       http://docs.python.org/2/distutils/setupscript.html

setup(
    name='permset',
    version='0.22',
    packages = ["permset"],
    description = "Simple standalone utility script to manage \*nix permissions on file and directory trees based on patterns.",
    author = "Robert Lujo",
    author_email = "trebor74hr@gmail.com",
    url = "https://github.com/trebor74hr/permset",
    scripts = ["scripts/permset"],
    long_description = long_description,
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


