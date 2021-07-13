from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()

# Get the long description from the README file
long_description = (here / 'README.md').read_text(encoding='utf-8')

setup(
    name            = 'renumSeq',
    version         = '1.1.0',
    description='Tool to renumber image sequences.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url             = 'https://github.com/jrowellfx/renumSeq',
    author          = 'James Philip Rowell',
    author_email    = 'james@alpha-eleven.com',

    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: BSD License',
        'Operating System :: POSIX',
        'Operating System :: Unix',
        'Operating System :: MacOS',
        'Development Status :: 5 - Production/Stable',
    ],

    packages        = ['renumseq'],
    python_requires = '>=3.6, <4',
    install_requires=['seqLister'],

    entry_points = {
        'console_scripts': [
            'renumseq = renumseq.__main__:main',
        ]
    }
)
