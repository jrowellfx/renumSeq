# About renumseq

`renumseq` is a Unix/Linux command-line-utility for renumbering image-sequences
which are most
typically used in CG post-production.

`renumseq` allows you to renumber sequences with an offset, or give them a new 'start' frame.
It also allows you adjust the padding of the frame numbers.

`renumseq` borrows the syntax of the native output of
[`lsseq`](https://github.com/jrowellfx/lsseq) to specify
the sequence to be renumbered. Therefore it is recommended to
also install `lsseq` as it makes using `renumseq` easier.

For example, use `lsseq` to list a sequence, then
cut and paste its
output as the arguments to `renumseq` with appropriate optional
arguments for setting the offset etc.

`renumseq` was written to be safe in that it won't
unintentionally overwrite any existing files
during the renumbering.  If
`renumseq` finds that by renumbering a sequence it will write over another frame
outside the range specified then it will skip renumbering that sequence
(printing a warning) and go onto the next sequence in the list.  Naturally
there is an option to force `renumseq` to overwrite those files if desired.

`renumseq` doesn't need to make temporary copies of files during the renumbering
(it does a move of the file), so it's fast.

`renumseq` also has a useful option, called `--replaceUnderscore` to change files of this form:

```
    filename_[n-m].extension
```

...to this,


```
    filename.[n-m].extension
```

which, as you can see, replaces the underscore-separator with a dot-separator.  
`Protip`: If all you want to do is switch the separator from an underscore to a dot, then
use a zero offset, plus the `--replaceUnderscore` argument.

## Installing renumseq

```
python3 -m pip install renumSeq
```

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

Alternatively you can just enclose the argument in quotes like we did above: `'aaa.[001-005].tif'`.

Type this:

```
$ renumseq --help
```

...for much more useful info.

Please contact j a m e s \<at\> a l p h a - e l e v e n . c o m with any bug
reports, suggestions or praise as the case may be.
