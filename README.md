# About renumseq

`renumseq` is a Unix/Linux/MacOS command-line-utility for renumbering image-sequences
which are most
typically used in VFX post-production or CG animation production.

`renumseq` allows you to renumber sequences with an offset or give them a new `start` frame.
It also allows you adjust the padding of the frame numbers.

`renumseq` has an especially helpful option, namely `--rename`, to allow you to rename
a sequence. See `--help` for details.

`renumseq` uses the syntax of the native output of
[`lsseq`](https://github.com/jrowellfx/lsseq) to specify
the sequence to be renumbered. Therefore it is recommended to
use `lsseq` as it makes using `renumseq` easier.

For example, use `lsseq` to list a sequence, then
cut and paste its
output as the arguments to `renumseq` with the appropriate 
arguments for setting the offset or new start-frame.

`renumseq` was written to be safe in that it won't
unintentionally overwrite any existing files
during renumbering.

If `renumseq` finds that by renumbering a sequence it will write over another frame
outside the range specified then it will skip renumbering that sequence
(printing a warning) and go onto the next sequence in the list.  Naturally
there is an option to force `renumseq` to overwrite those files if desired.

`renumseq` doesn't need to make temporary copies of files during the renumbering
(it does a move of the file), so it's fast.

`renumseq` also has a useful option, called `--replace-underscore`
that changes any underscore-separators (separating the filename from the
frame-number) with dot-separators, like this:  

`filename_[n-m].extension` -> `filename.[n-m].extension`

`Protip`: If all you want to do is switch the separator from an underscore to a dot, then
use a zero offset, plus the `--replace-underscore` argument.

## Installing renumseq

```
python3 -m pip install renumSeq --upgrade
```
If installing locally, it's probably best to install in a virtual-environment
or [`venv`](https://docs.python.org/3/library/venv.html). 

There is additional installation-information in an
[addendum](https://github.com/jrowellfx/lsseq#addendum---more-on-installing-command-line-tools)
in the `lsseq` repo with a helpful technique for installing `renumseq` system-wide.

## Testing renumseq

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

Note that you may get an error from your
shell when you try to run the `renumseq` command above, without the
quotes around the sequence, that might look something like
this:

```
% renumseq -o 10 aaa.[001-005].tif
renumseq: No match.
```

In which case you need to "escape" the square brackets as they are special characters
as far as the shell is concerned. Escape them like this:

```
% renumseq -v -o 10 aaa.\[001-005\].tif
aaa.005.tif -> aaa.015.tif
aaa.004.tif -> aaa.014.tif
aaa.003.tif -> aaa.013.tif
aaa.002.tif -> aaa.012.tif
aaa.001.tif -> aaa.011.tif
```

Alternatively you can just enclose the argument in quotes
(`'aaa.[001-005].tif'`)
like we did in the example above.

## `renumseq --help`
A full listing of all the command-line options follows, as displayed when running `renumseq --help`.

```
usage: renumseq [-h | --help] [OPTION]... [SEQ]...

Renumber the frame range of each SEQ listed on the command line.
SEQ should be specified using lsseq's native format.

Protip: Enclosing SEQ in quotes will turn off the special
treatment of '[' and ']' by the shell.

Example usage:
    $ lsseq
    aaa.[001-005].tif
    $ renumseq -o 10 'aaa.[001-005].tif'
    $ lsseq
    aaa.[011-015].tif

positional arguments:
  SEQ                   image sequence in lsseq native format

optional arguments:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  --start START_FRAME   Use START_FRAME as the first frame number of each SEQ.
                        This takes precedence over --offset
  --offset FRAME_OFFSET, -o FRAME_OFFSET
                        offset SEQ by this number of frames (can be negative).
                        Frame i becomes i + FRAME_OFFSET
  --skip                if renumbering a file in SEQ would result in
                        overwriting an existing file (which isn't also being
                        renumbered) then skip renumbering SEQ altogether.
                        [default] The opposite of --force.
  --force               if renumbering a file in SEQ would result in
                        overwriting an existing file (which isn't also being
                        renumbered) then overwrite the file. The opposite of
                        --skip
  --pad PAD             set the padding of the frame numbers to be PAD digits.
                        The default action is to leave the padding unchanged.
                        Note, lsseq's native format output properly lists the
                        sequence range with appropriate padding.
  --rename NEW_SEQNAME  Rename the DESCRIPTIVE_NAME part of SEQ from its
                        existing name to NEW_SEQNAME. When using this option
                        then the command will exit with an error unless
                        exactly one SEQ is being renamed and/or renumbered.
  --replace-underscore  in the case that SEQ uses an underscore ('_')
                        separating the filename from the frame number; then
                        when renumbering SEQ, replace the underscore with a
                        dot-separator ('.'). Note that you can use an offset
                        of zero (default) to replace the underscore with a dot
                        leaving all else the same
  --touch [[CC]YYMMDD[-hh[mm[ss]]]]
                        If no date is provided then update the access time of
                        the files being renumbered to the current time.
                        Otherwise, use the date provided to update the file's
                        access time. The optional CC (century) defaults to the
                        current century and '-hh' (hours), 'mm' (minutes) or
                        'ss' (seconds) default to zero if not specified. Note:
                        the default action is to leave the access time of the
                        SEQ unchanged.
  --dry-run             Don't renumber SEQ, just display how the files would
                        have been renumbered. Forces --verbose
  --silent, --quiet, -s
                        suppress all errors and warnings
  --verbose, -v         list the mapping from old file-name to new file-name
```
## Error and warning codes returned from `renumseq`

As copied from the source code,
the following EXIT codes will be combined bitwise to return
possibly more than one different warning and/or error.

```
EXIT_NO_ERROR                 =   0 # Clean exit.
EXIT_PREEXISTINGSEQ_ERROR     =   1 # Attempting to rename seq to one that already exists.
EXIT_ARGPARSE_ERROR           =   2 # Parsing an argument revealed an error.
EXIT_NULLACTION_WARNING       =   4 # Exited with nothing to do.
EXIT_INVALIDRANGE_WARNING     =   8 # Invalid frame-range specified for a sequence
EXIT_NOTASEQ_WARNING          =  16 # Expecting a sequence, but doesn't appear to be one.
EXIT_NONEXISTENTSEQ_WARNING   =  32 # Specified sequence does not exist.
EXIT_OVERWRITEFRAME_WARNING   =  64 # Renumbering a sequence would
                                    # have over-written some frames outside the range specifed.
```

# Important: latest MAJOR point release of `renumSeq`.

`renumseq` and all the utilities provided by jrowellfx github repos
use "[`Semantic Versioning 2.0.0`](https://semver.org/)" in numbering releases.
The latest release of `renumseq` upped the `MAJOR` release number
from `v1.x.x` to `v2.x.x`.

While the functionality and output of `renumseq` has not changed, all the so called
"long options" have been renamed to adhere to `POSIX` standard naming
conventions.

That is, prior to `v2.0.0` of `renumseq` all the long-option names used a "camel case"
naming convention but as of `v2.0.0` all long-option names have been
changed to so-called "kebab case".

For example:

```
--replaceUnderscore
```

has been changed to

```
--replace-underscore
```

In the event that you have written any scripts that make use of `renumseq` or
any other of `jrowellfx`'s utils provided [here](https://github.com/jrowellfx) 
you will need to edit your scripts to be able to update to the lastest versions
of the utilities.

In this case, in order to assist in switching to the
current `MAJOR` point release some `sed` scripts have been provided that should make
the transition quite painless. Especially if you make use
of [`runsed`](https://github.com/jrowellfx/vfxTdUtils) which if you haven't used it before,
now is the time, it's extremely helpful.

There are two files provided at the root-level of the repo, namely:
`sed.script.jrowellfx.doubleDashToKebab` and `sed.script.renumseq.v1tov2`.

The first one can be used to fix the long-option names for ALL the 
`MAJOR` point release updates to the long-options in any of `jrowellfx`'s utilities.
The second one contains only changes needed for the updates to `renumseq`.

## Example `sed.script` usage.

Download one or both of the sed scripts named above. Make sure you have `runsed` installed
on your system. (Example applied to usage of `lsseq` but it's the same idea for `renumseq`.)

```
$ cd ~/bin
$ ls
myScriptThatUsesLsseq  sed.script.jrowellfx.doubleDashToKebab
$ cat myScriptThatUsesLsseq
#!/bin/bash

lsseq --globalSortByTime --recursive --prependPathAbs /Volumes/myProjectFiles

$ runsed -f sed.script.jrowellfx.doubleDashToKebab myScriptThatUsesLsseq
$ ./.runsed.diff.runsed
+ /usr/bin/diff ./.myScriptThatUsesLsseq.runsed myScriptThatUsesLsseq
3c3
< lsseq --globalSortByTime --recursive --prependPathAbs /Volumes/myProjectFiles
---
> lsseq --global-sort-by-time --recursive --prepend-path-abs /Volumes/myProjectFiles
$ cat myScriptThatUsesLsseq
#!/bin/bash

lsseq --global-sort-by-time --recursive --prepend-path-abs /Volumes/myProjectFiles
```

Note that if you are unhappy with the changes you can undo them easily with

```
$ ./.runsed.undo.runsed
$ cat myScriptThatUsesLsseq
#!/bin/bash

lsseq --globalSortByTime --recursive --prependPathAbs /Volumes/myProjectFiles
```

## Contact

Please contact `j a m e s <at> a l p h a - e l e v e n . c o m` with any bug
reports, suggestions or praise as the case may be.

