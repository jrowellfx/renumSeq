#!/usr/bin/python2.7

from distutils.core import setup
import os
import shutil

setup(name='renum',
      version='1.012',
      description='tool to renumber image sequences',
      long_description='Uses lsseq native format to specify sequence to renumber - with various options.  Very safe in terms on not overwriting files accidentally. lsseq must be installed on the system as renum uses a python library (seqLister) that is installed by that package',
      author='James Philip Rowell',
      author_email='james@alpha-eleven.com',
      url='http://www.alpha-eleven.com/',
      py_modules=[],
      scripts=['renum'],
      license = "BSD 3-Clause license",
     )
