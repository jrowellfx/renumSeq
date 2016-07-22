.ll 76
.na
.hy 0
.pl 1
renum is one of those basic utilities that one needs around a CG production studio.
renum is for renumbering frame sequences.
Surprisingly a good version of this command doesn't exist in the public domain,
so this version of renum should forever fill that need.

renum allows you to renumber sequences, and optionally adjust the padding of the
frame numbers. renum relies on the util lsseq also having been installed on
your system as renum uses a library provided by the lsseq package. Furthermore,
renum uses the syntax of the native output of lsseq to specify the sequence to be renumbered.
Having this connection to lsseq makes it pretty easy to run renum, cutting and 
pasting output from lsseq to the arguments of renum with appropriate optional arguments
setting the amount of frames to offset the sequence by etc.

renum was written to be quite safe in that it first checks to see if it's safe to rename
the ALL files with the new frame numbers before actually renaming any files.  That is, if it
finds that by renumbering a sequence you will write over another frame outside the range
specified then it will skip renumbering
that sequence (printing a warning) and go onto the next sequence in the list.

renum also has a handy use to optionally change files of this form:

.ti 4
<filename>_[n-m].extension

\&... by replacing the underscore separator to be a dot so that the filenames are this:

.ti 4
<filename>.[n-m].extension

To install renum on your system follow these steps (you need
root privileges).

First install the latest version of lsseq on your system. You can get it from jrowellfx's github repo.

n +3
.ti -3
1) Download renum-1.000.tar.gz
assuming that the latest version is 1.000 (if not
just grab the latest one).

.ti -3
2) Uncompress the file:
.nf
$ tar -xvf renum-1.000.tar.gz
.fi

.ti -3
3) install the command
.nf
$ cd renum-1.000
$ sudo python setup.py install
.fi

.ti -3
4) ...that's it! You should be able to run the commands "renum" now
.in -3

To test renum try the following:

.nf
$ cd ~
$ mkdir tmp
$ cd tmp
$ touch aaa.001.tif aaa.002.tif aaa.003.tif aaa.004.tif aaa.005.tif
$ lsseq -Z
aaa.[001-005].tif
$ renum --verbose --offset 10 aaa.[001-005].tif
aaa.005.tif -> aaa.015.tif
aaa.004.tif -> aaa.014.tif
aaa.003.tif -> aaa.013.tif
aaa.002.tif -> aaa.012.tif
aaa.001.tif -> aaa.011.tif
$ lsseq -Z
aaa.[011-015].tif 
.fi

Note that if you are using the tcsh then you may get an error from
your shell when you try to run the renum command, that might
look something like this:

.nf
% renum -o 10 aaa.[001-005].tif 
renum: No match.
.fi

In which case you need to "escape" the square brackets as tcsh is using them
for globbing. i.e.; like this:

.nf
% renum -v -o 10 aaa.\\[001-005\\].tif 
aaa.005.tif -> aaa.015.tif
aaa.004.tif -> aaa.014.tif
aaa.003.tif -> aaa.013.tif
aaa.002.tif -> aaa.012.tif
aaa.001.tif -> aaa.011.tif
.fi

Helpful hint: ditch tcsh! Use bash, it's so much better. :-)

Also try this:

.nf
$ renum --help
.fi

for much more useful info.

Please contact j a m e s <at> o i c - i n c . n e t with any bug reports, suggestions
or oodles of praise as the case may be.

