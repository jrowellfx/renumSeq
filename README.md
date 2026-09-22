# About renumseq

[![PyPI version](https://img.shields.io/pypi/v/renumSeq.svg)](https://pypi.org/project/renumSeq/)

`renumseq` is a `Unix/Linux/MacOS` command-line utility for renumbering
image-sequences, most typically used in VFX post-production or CG animation
production.

`renumseq` allows you to renumber sequences with an offset or give them a
new `start` frame. It also allows you to adjust the padding of the frame
numbers, and, with `--rename`, to rename a sequence's descriptive name.

`renumseq` uses the syntax of the native output of
[`lsseq`](https://github.com/jrowellfx/lsseq) to specify
the sequence to be renumbered. Therefore it is recommended to
use `lsseq` alongside `renumseq` — list a sequence with `lsseq`, then cut
and paste its output as the argument to `renumseq`.

`renumseq` was written to be safe: it won't unintentionally overwrite any
existing files during renumbering. If renumbering a sequence would write
over a frame outside the range specified, `renumseq` skips that sequence
(printing a warning) and moves on to the next one — see `--force` below to
override this.

`renumseq` doesn't need to make temporary copies of files during
renumbering (it does a move of each file), so it's fast, and, by default,
leaves file timestamps untouched — see `--touch` below for how to opt into
changing them.

## Table of Contents

- [Installing renumseq](#installing-renumseq)
  - [Testing installation](#testing-installation)
- [Usage examples](#usage-examples)
- [`renumseq --help`](#renumseq---help)
- [Error and warning codes returned by renumseq](#error-and-warning-codes-returned-by-renumseq)
- [Addendum - more on installing command-line tools and man pages](#addendum---more-on-installing-command-line-tools-and-man-pages)
  - [Installing the command-line tools](#installing-the-command-line-tools)
    - [Helpful hint: Upgraded the system-wide default version of python3?](#helpful-hint-upgraded-the-system-wide-default-version-of-python3)
  - [Installing the renumseq(1) man page](#installing-the-renumseq1-man-page)
    - [Customizing the man page install location](#customizing-the-man-page-install-location)
    - [Troubleshooting: `man renumseq` says "No manual entry"](#troubleshooting-man-renumseq-says-no-manual-entry)
- [Changelog](#changelog)
  - [v3.0.0 - removed `-s` short option from `--silent` (MAJOR, breaking)](#v300---removed--s-short-option-from---silent-major-breaking)
  - [v2.0.0 - long options renamed to kebab-case (MAJOR, breaking)](#v200---long-options-renamed-to-kebab-case-major-breaking)
    - [Example `sed.script` usage](#example-sedscript-usage)
- [Contact](#contact)

## Installing renumseq

```
    python3 -m pip install renumSeq --upgrade
```
If installing locally, it's probably best to install in a virtual-environment
or [`venv`](https://docs.python.org/3/library/venv.html).

There is additional installation-information in an
[addendum](https://github.com/jrowellfx/renumSeq#addendum---more-on-installing-command-line-tools-and-man-pages)
below with a helpful technique for installing `renumseq` system-wide, and
for installing the `renumseq(1)` man page.

### Testing installation

After installing try the following:

```
    $ cd ~
    $ mkdir tmp
    $ cd tmp
    $ touch aaa.001.tif aaa.002.tif aaa.003.tif aaa.004.tif aaa.005.tif
    $ lsseq -Z
    aaa.[001-005].tif
    $ renumseq --verbose --offset 10 'aaa.[001-005].tif'
    aaa.005.tif -> aaa.015.tif
    aaa.004.tif -> aaa.014.tif
    aaa.003.tif -> aaa.013.tif
    aaa.002.tif -> aaa.012.tif
    aaa.001.tif -> aaa.011.tif
    $ lsseq -Z
    aaa.[011-015].tif
```

Note that you may get an error from your shell when you try to run the
`renumseq` command above, without the quotes around the sequence, that
_might_ look something like this:

```
    $ renumseq -o 10 aaa.[001-005].tif
    renumseq: No match.
```

In which case you need to "escape" the square brackets as they are usually
treated as special
characters as far as the shell is concerned. Escape them like this:

```
    # Note: shortform-options for --verbose and --offset below
    $ renumseq -v -o 10 aaa.\[001-005\].tif
    aaa.005.tif -> aaa.015.tif
    aaa.004.tif -> aaa.014.tif
    aaa.003.tif -> aaa.013.tif
    aaa.002.tif -> aaa.012.tif
    aaa.001.tif -> aaa.011.tif
```
Alternatively you can just enclose the argument in quotes
(`'aaa.[001-005].tif'`) like we did in the example above.

## Usage examples

Beyond a simple offset, `renumseq` can retarget a sequence to an explicit
start frame. We can also change its padding if we like, all in one pass:

```
    $ lsseq
    aaa.[1-10].jpg
    $ renumseq --start 995 --pad 4 'aaa.[1-10].jpg'
    $ lsseq
    aaa.[0995-1004].jpg
```

The option `--rename` renames a sequence's descriptive name in place, and can be
combined with any of the other options above:

```
    $ lsseq
    aaa.[005-015].tif
    $ renumseq --start 995 --pad 4 --rename bbb 'aaa.[005-015].tif'
    $ lsseq
    bbb.[0995-1005].tif
```

The option `--replace-underscore` changes an underscore-separator
to a dot-separator, so `filename_[n-m].extension` would
become `filename.[n-m].extension`.

`Protip`: If all you want to do is switch the separator from an underscore
to a dot, use a zero offset plus `--replace-underscore`, like this:

```
$ lsseq
ccc_10.jpg  ccc_12.jpg	ccc_14.jpg  ccc_5.jpg  ccc_7.jpg  ccc_9.jpg
ccc_11.jpg  ccc_13.jpg	ccc_15.jpg  ccc_6.jpg  ccc_8.jpg
$ lsseq --loose-num-separator
ccc_[5-15].jpg
$ renumseq --offset 0 --replace-underscore 'ccc_[5-15].jpg'
$ lsseq
ccc.[5-15].jpg

```

Before running anything for real, `--dry-run` (implies `--verbose`) which
shows exactly what would happen without touching any files:

```
$ lsseq
aaa.[001-010].jpg
$ renumseq --dry-run --offset 50 --rename xxx 'aaa.[001-010].jpg'
aaa.010.jpg -> xxx.060.jpg
aaa.009.jpg -> xxx.059.jpg
aaa.008.jpg -> xxx.058.jpg
aaa.007.jpg -> xxx.057.jpg
aaa.006.jpg -> xxx.056.jpg
aaa.005.jpg -> xxx.055.jpg
aaa.004.jpg -> xxx.054.jpg
aaa.003.jpg -> xxx.053.jpg
aaa.002.jpg -> xxx.052.jpg
aaa.001.jpg -> xxx.051.jpg
$ lsseq
aaa.[001-010].jpg
```

Lastly try `renumseq --help` to see a full listing of all the command-line options,
or `man renumseq` if you install the man-page as described in the addendum below.

## Addendum - more on installing command-line tools and man pages

Here's the process that I've followed to install `renumseq`, as well as my
other python-based command-line tools (i.e.,
[`lsseq`](https://github.com/jrowellfx/lsseq),
[`expandseq`](https://github.com/jrowellfx/expandSeq),
[`condenseseq`](https://github.com/jrowellfx/expandSeq) and
[`fixSeqPadding`](https://github.com/jrowellfx/fixSeqPadding))
so that they are accessible to all users. This works on both MacOS and
Linux.

### Installing the command-line tools

```
    $ su -
    # cd /usr/local
    # python3 -m venv venv
    # cd venv
    # source bin/activate
    # python3 -m pip install --upgrade pip
    # deactivate
    # bin/pip install lsseq --upgrade
    # bin/pip install renumSeq --upgrade
    # bin/pip install expandSeq --upgrade
    # bin/pip install fixSeqPadding --upgrade
    # ln -s /usr/local/venv/bin/lsseq /usr/local/bin/lsseq
    # ln -s /usr/local/venv/bin/renumseq /usr/local/bin/renumseq
    # ln -s /usr/local/venv/bin/expandseq /usr/local/bin/expandseq
    # ln -s /usr/local/venv/bin/condenseseq /usr/local/bin/condenseseq
    # ln -s /usr/local/venv/bin/fixseqpadding /usr/local/bin/fixseqpadding
    # exit
    $ renumseq --version
    3.0.0
```

At this point any user should be able to run any of the commands linked in
the example above. Note that updates are easy too. Say there's an update to
`renumseq` that you want to install.

```
    $ su -
    # cd /usr/local/venv
    # bin/pip install renumSeq --upgrade
    # exit
    $ renumseq --version
    99.99.99
```

Just kidding about the version number, maybe in the year 2159? Will Unix
still be a thing!?

#### Helpful hint: Upgraded the system-wide default version of python3?

Say you had installed `renumseq` as described above, while the default
`python3` was linked to `python3.6`. Then suppose the system default
`python3` was then linked to a higher version of python
(check with: `python3 --version`). At that point running `renumseq` might
error out like this:

```
Traceback (most recent call last):
  File "/usr/local/bin/renumseq", line 5, in <module>
    from renumseq.__main__ import main
ModuleNotFoundError: No module named 'renumseq'
```
This is an easy problem to fix. Delete (or move to a backup location) the
entire directory `/usr/local/venv` and redo the steps above to install
`lsseq`, `renumseq`, `expandseq`, etc. from scratch.

### Installing the renumseq(1) man page

`pip` has no mechanism for installing man pages, so `renumseq`'s man page
(`man/renumseq.1` in this repo) is installed separately, via a small
`Makefile` provided at the root of the repo. This is a one-time step
independent of however you installed the `renumseq` command itself (via
`pip`, the venv setup above, or otherwise) — it just needs to be run once
per machine, and again whenever the man page itself is updated.

```
    $ git clone https://github.com/jrowellfx/renumSeq.git
    $ cd renumSeq
    $ sudo make install
    $ man renumseq
```

`sudo` (or being root, as in the venv setup above) is only needed because
the default install location, `/usr/local/share/man/man1`, is a system
directory. That location is on the default `MANPATH` on both MacOS and most
Linux distributions, so no further configuration is normally required.

To remove it again:

```
    $ sudo make uninstall
```

#### Customizing the man page install location

A few variables can be overridden on the `make` command line for less
typical setups:

```
    # Install under a different prefix, e.g. if you keep tools in /usr:
    $ sudo make install PREFIX=/usr

    # Install to a user-writable location, no sudo required, provided
    # that location's man directory is already on your MANPATH:
    $ make install PREFIX=$HOME/.local

    # Install a gzip-compressed man page instead (some distros prefer this;
    # `man` reads either form transparently):
    $ sudo make install-compressed

    # Stage the install into a temporary root, e.g. when building a
    # package, keeping PREFIX as the eventual install location:
    $ make install DESTDIR=/tmp/pkgroot PREFIX=/usr/local
```

Run `make` with no target for a summary of these options.

#### Troubleshooting: `man renumseq` says "No manual entry"

This almost always means the install location isn't on your `MANPATH`, or
your system's man-page cache is stale. Try:

```
    $ manpath
```

to see the directories `man` actually searches, and confirm the install
location (`/usr/local/share/man/man1` by default) is among them. On Linux,
refreshing the cache with `sudo mandb` after installing usually resolves
it; MacOS does not require this step.

## Error and warning codes returned by renumseq

As copied from the source code, the following EXIT codes are combined
bitwise, so a single run can report more than one condition at once.

```
EXIT_NO_ERROR                 =   0 # Clean exit.
EXIT_PREEXISTINGSEQ_ERROR     =   1 # Attempting to rename seq to one that already exists.
EXIT_ARGPARSE_ERROR           =   2 # Parsing an argument revealed an error.
EXIT_NULLACTION_WARNING       =   4 # Exited with nothing to do.
EXIT_INVALIDRANGE_WARNING     =   8 # Invalid frame-range specified for a sequence
EXIT_NOTASEQ_WARNING          =  16 # Expecting a sequence, but doesn't appear to be one.
EXIT_NONEXISTENTSEQ_WARNING   =  32 # Specified sequence does not exist.
EXIT_OVERWRITEFRAME_WARNING   =  64 # Renumbering a sequence would have
                                     # over-written some frames outside the range specified.
```

## Changelog

`renumseq` and all the utilities provided by jrowellfx github repos use
"[`Semantic Versioning 2.0.0`](https://semver.org/)" in numbering releases.
This section documents notable and breaking changes, most recent first.

### v3.0.0 - removed `-s` short option from `--silent` (MAJOR, breaking)

The `-s` short form of `--silent` was removed; the long forms `--silent`
and `--quiet` are unaffected and unchanged. This was a deliberately
breaking change, made specifically to free up `-s` for reuse as a shorthand
for `--start` in a future release.

If you have scripts using `renumseq -s`, replace it with
`renumseq --silent`.

### v2.0.0 - long options renamed to kebab-case (MAJOR, breaking)

While the functionality and output of `renumseq` did not change, all the
so-called "long options" were renamed to adhere to `POSIX` standard naming
conventions.

That is, prior to `v2.0.0` of `renumseq` all the long-option names used a
"camel case" naming convention but as of `v2.0.0` all long-option names
were changed to so-called "kebab case".

For example:

```
--replaceUnderscore
```

was changed to

```
--replace-underscore
```

If you have written any scripts that make use of `renumseq` or any other of
`jrowellfx`'s utils provided [here](https://github.com/jrowellfx), and
haven't updated them since, you will need to edit your scripts to be able
to update to current versions of the utilities.

To assist in switching to the `v2.0.0` naming, some `sed` scripts were
provided that should make the transition quite painless. Especially if you
make use of [`runsed`](https://github.com/jrowellfx/vfxTdUtils) which if
you haven't used it before, now is the time, it's extremely helpful.

There are two files provided at the root-level of the repo, namely:
`sed.script.jrowellfx.doubleDashToKebab` and `sed.script.renumseq.v1tov2`.

The first one can be used to fix the long-option names for ALL the
`v2.0.0`-era updates to the long-options in any of `jrowellfx`'s
utilities. The second one contains only changes needed for the updates to
`renumseq`.

## Contact

Please contact `j a m e s <at> a l p h a - e l e v e n . c o m` with any bug
reports, suggestions or praise as the case may be.
