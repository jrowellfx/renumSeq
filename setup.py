from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()

# Get the long description from the README file
long_description = (here / 'README.md').read_text(encoding='utf-8')

# Semantic Versioning 2.0.0
#
# MAJOR version for incompatible API changes
# MINOR version for added functionality in a backwards compatible manner
# PATCH version for backwards compatible bug fixes

setup(
    name            = 'renumSeq',
    version         = '2.1.0',
    description='Tool to renumber image sequences.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url             = 'https://github.com/jrowellfx/renumSeq',
    author          = 'James Philip Rowell',
    author_email    = 'james@alpha-eleven.com',
    license         = "BSD-3-Clause",
    license_files = ["LICENSE"],

    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: POSIX',
        'Operating System :: Unix',
        'Operating System :: MacOS',
        'Development Status :: 5 - Production/Stable',
    ],

    packages        = ['renumseq'],
    python_requires = '>=3.7, <4',
    install_requires=['seqLister>=1.2.0', 'lsseq>=4.0.0'],

    entry_points = {
        'console_scripts': [
            'renumseq = renumseq.__main__:main',
        ]
    }
)
