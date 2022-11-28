#!/usr/bin/env python3

# 3-Clause BSD License
# 
# Copyright (c) 2008-2022, James Philip Rowell,
# Alpha Eleven Incorporated
# www.alpha-eleven.com
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
#  1. Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
# 
#  2. Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer in
#     the documentation and/or other materials provided with the
#     distribution.
# 
#  3. Neither the name of the copyright holder, "Alpha Eleven, Inc.",
#     nor the names of its contributors may be used to endorse or
#     promote products derived from this software without specific prior
#     written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT
# HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# renumseq - renumber images sequences on the command line
#         specify the sequences using lsseq's native format

import re
import argparse
import os, sys
import textwrap
import time
from datetime import datetime, timedelta, timezone
import seqLister

VERSION = "1.2.2"

touchTime = -1.0

def warnSeqSyntax(silent, basename, seq) :
    if not silent :
        print( os.path.basename(sys.argv[0]),
            ": warning: invalid range [", seq, "] for seq ", basename,
            file=sys.stderr, sep='')

def main():

    NEVER_START_FRAME = -999999999999
    touchFiles = False
    global touchTime


    # Redefine the exception handling routine so that it does NOT
    # do a trace dump if the user types ^C while renumseq is running.
    #
    old_excepthook = sys.excepthook
    def new_hook(exceptionType, value, traceback):
        if exceptionType != KeyboardInterrupt and exceptionType != IOError:
            old_excepthook(exceptionType, value, traceback)
        else:
            pass
    sys.excepthook = new_hook

    p = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent('''
            Renumber the frame range of each SEQ listed on the command line.
            SEQ should be specified using lsseq's native format.
            
            Protip: Turning off globbing, or enclosing SEQ in quotes, or placing
            backslashes ahead of '[' and ']' will be necessary to turn off the special
            treatment of '[' and ']' by the shell.

            Caution: The files in the sequence MUST BE correctly padded.
            Pay attention to lsseq's --showBadPadding for reports of badly padded frame
            numbers and fix them before renumbering a sequence with this utility.

            Example usage:
                $ lsseq
                aaa.[001-005].tif
                $ renumseq -o 10 'aaa.[001-005].tif'
                $ lsseq
                aaa.[011-015].tif
            '''),
        usage="%(prog)s [OPTION]... [SEQ]...")

    p.add_argument("--version", action="version", version=VERSION)

    p.add_argument("--start", action="store", type=int,
        dest="startFrame", default=NEVER_START_FRAME,
        metavar="START_FRAME",
        help="Use START_FRAME as the first frame number of each SEQ. \
        This takes precedence over --offset")
    p.add_argument("--offset", "-o", action="store", type=int,
        dest="offsetFrames", default=0,
        metavar="FRAME_OFFSET",
        help="offset SEQ by this number of frames (can be negative). \
        Frame i becomes i + FRAME_OFFSET")

    p.add_argument("--dryRun", action="store_true",
        dest="dryRun", default=False,
        help="Don't renumber SEQ, just display how the \
        files would have been renumbered. Forces --verbose" )
    p.add_argument("--skip", action="store_false",
        dest="clobber", default=False,
        help="if renumbering a file in SEQ would result in overwriting \
        an existing file (which isn't also being renumbered) \
        then skip renumbering SEQ altogether. [default] \
        The opposite of --force.")
    p.add_argument("--force", action="store_true",
        dest="clobber",
        help="if renumbering a file in SEQ would result in overwriting \
        an existing file (which isn't also being renumbered) \
        then overwrite the file. The opposite of --skip")

    # Note: the following default for "pad" of "-1" means to leave
    # the padding on any given frame sequence unchanged.
    #
    p.add_argument("--pad", action="store", type=int,
        dest="pad", default=-1,
        metavar="PAD",
        help="set the padding of the frame numbers to be PAD digits. \
        The default action is to leave the padding unchanged. Note, \
        lsseq's native format output properly lists the sequence \
        range with appropriate padding and can also report when there are \
        incorrectly padded frame-numbers with --showBadPadding")

    p.add_argument("--replaceUnderscore", action="store_true",
        dest="fixUnderscore", default=False,
        help="in the case that SEQ uses an underscore ('_') \
        separating the filename from the frame number; then when renumbering \
        SEQ, replace the underscore with a dot-separator ('.'). Note that \
        you can use an offset \
        of zero (default) to replace the underscore with a dot leaving all else the same")
    p.add_argument("--touch", nargs='?',
        dest="touch",
        default=None, # Value if --touch NOT present on cmd line.
        const="0",    # Value if --touch present but NO argument passed to it.
        metavar="[CC]YYMMDD[hhmm]",
        help="update the access time of the file being renamed to the \
        current time. Optionally specify a date for the updated access time. \
        Note: if this is the last argument on the command line and the optional \
        date was not specified then \
        append '--' before the list of SEQs to delineate the end of the options")
    p.add_argument("--silent", "--quiet", "-s", action="store_true",
        dest="silent", default=False,
        help="suppress all errors and warnings")
    p.add_argument("--verbose", "-v", action="store_true",
        dest="verbose", default=False,
        help="list the mapping from old file-name to new file-name")

    p.add_argument("files", metavar="SEQ", nargs="*",
        help="image sequence in lsseq native format")

    args = p.parse_args()

    
    if args.files == [] :
        sys.exit(0)

    # The following logic means "do nothing" - so just exit cleanly (**a**)
    #
    if args.offsetFrames == 0 \
            and args.pad < 0 \
            and not args.fixUnderscore \
            and args.startFrame == NEVER_START_FRAME :
        if not args.silent :
            print(os.path.basename(sys.argv[0]),
                ": warning: no offset, no padding change etc., nothing to do",
                file=sys.stderr, sep='')
        sys.exit(0)

    if args.touch != None : # --touch called
        touchFiles = True
        if args.touch == "0" : # Touch with current time.
            touchTime = 0.0
        else :
            # Temporary - parse this with string passed in.
            touchTime = datetime.timestamp(datetime(2001, 6, 1, 12, 30))

    if args.dryRun : # verbose to show how renumbering would occur.
        args.verbose = True

    # The following regular expression is created to match lsseq native sequence syntax
    # which means (number labels refer to parenthesis groupings **):
    #
    # 0 - one or more of anything,           followed by
    # 1 - a dot or underscore,               followed by
    #     an open square bracket,            followed by
    # 2 - a frame range,                     followed by
    #     a close square bracket then a dot, followed by
    # 3 - one or more letters, optionally one dot,
    #     then one or more letters, then one or more letters and numbers
    #     and the end of the line.
    #
    pattern = re.compile(r"(.+)([._])\[(-?[0-9]+-?-?[0-9]+)\]\.([a-zA-Z]+\.?[a-zA-Z]+[a-zA-Z0-9]*$)")

    for arg in args.files :
        abortSeq = False

        # Check if 'arg' is a sequence in valid lsseq native format
        #
        match = pattern.search(arg)
        if not match :
            if not args.silent :
                print(os.path.basename(sys.argv[0]), ": warning: ", arg,
                    " not a sequence or not in lsseq native format",
                    file=sys.stderr, sep='')
            continue

        v = match.groups()

        usesUnderscore = (v[1] == '_')
        seq = [v[0], v[2], v[3]] # base filename, range, file-extension. (see above **)

        # seq might be range with neg numbers. Assume N,M >= 0,
        # then there are only 5 seq cases that we need to be
        # concerned with: N, -N, N-M, -N-M, -N--M,
        # where -N or N is always less than or equal to -M or M.
        #
        negStart = 1
        negEnd = 1
        startStr = ""
        endStr = ""
        frRange = seq[1].split("-")

        if len(frRange) > 4 :
            warnSeqSyntax(args.silent, seq[0], seq[1])
            continue # Invalid syntax for range

        if len(frRange) == 1 : # Just N
            startStr = frRange[0]
            endStr = frRange[0]

        elif len(frRange) == 2 : # minus-N OR N-M
            if frRange[0] == '' : # Leading minus sign.
                negStart = -1
                negEnd = -1
                startStr = frRange[1]
                endStr = frRange[1]
            else :
                startStr = frRange[0]
                endStr = frRange[1]

        elif len(frRange) == 3 : # neg-N to M
            if frRange[0] != '' : # Not leading minus sign!
                warnSeqSyntax(args.silent, seq[0], seq[1])
                continue # Invalid syntax for range
            negStart = -1
            startStr = frRange[1]
            endStr = frRange[2]

        elif len(frRange) == 4 : # neg-N to neg-M
            if frRange[0] != '' or frRange[2] != '' : # Not leading minus signs!
                warnSeqSyntax(args.silent, seq[0], seq[1])
                continue # Invalid syntax for range
            negStart = -1
            negEnd = -1
            startStr = frRange[1]
            endStr = frRange[3]

        try :
            start = int(startStr)
        except ValueError : # Invalid syntax for range
            warnSeqSyntax(args.silent, seq[0], seq[1])
            continue

        try :
            end = int(endStr)
        except ValueError : # Invalid syntax for range
            warnSeqSyntax(args.silent, seq[0], seq[1])
            continue

        start *= negStart
        end *= negEnd

        if start > end :
            warnSeqSyntax(args.silent, seq[0], seq[1])
            continue

        # If args.startFrame is used, it will override 
        # args.offsetFrames.
        #
        if args.startFrame != NEVER_START_FRAME :

            args.offsetFrames = args.startFrame - start

            # This duplicates the test above (**a**) because now
            # we might have a zero offset for this sequence.
            # Instead of exiting we just skip to the next seq.
            #
            if args.offsetFrames == 0 \
                    and args.pad < 0 \
                    and not args.fixUnderscore :
                if not args.silent :
                    print(os.path.basename(sys.argv[0]),
                        ": warning: no offset, no padding/underscore change, skipping sequence: ",
                        arg, file=sys.stderr, sep='')
                continue

        startPad = len(startStr)
        if negStart < 0 :
            startPad += 1
        endPad = len(endStr)
        if negEnd < 0 :
            endPad += 1

        currentPad = 0
        if startPad < endPad :
            currentPad = startPad
        else :
            currentPad = endPad
        newPad = currentPad

        if args.pad >= 0 :
            newPad = args.pad

        currentFormatStr = "{0:0=-" + str(currentPad) + "d}"
        newFormatStr = "{0:0=-" + str(newPad) + "d}"

        frameList = seqLister.expandSeq(seq[1])

        if frameList == [] :
            warnSeqSyntax(args.silent, seq[0], seq[1])
            continue # Invalid syntax for range

        frameList.sort(reverse=(args.offsetFrames > 0))

        origNames = []
        newNames = []
        checkNames = []

        if usesUnderscore :
            currentSeparator = '_'
            if args.fixUnderscore :
                newSeparator = '.'
            else :
                newSeparator = '_'
        else :
            currentSeparator = '.'
            newSeparator = '.'

        # Note, that if SEQ has some frames with bad-padding(*), then creating the
        # filename 'origFile' below will make a name that doesn't match the file on
        # disk so it will be treated like it doesn't exist.
        #
        # This will likely lead to unexpected results as far as the user is concerned.
        # Worst case: A rare combination of circumstances COULD lead to the badly padded
        # filename being overwritten unintentionally.
        #
        # E.g.: renumbering the sequence 'a.[098-102].exr p:[99]', i.e.,
        #    a.098.exr, a.99.exr, a.100.exr a.101.exr, a.102.exr
        # with '--offset -2 --force --pad 2' will make a new sequence:
        #    a.96.exr, a.98.exr, a.99.exr, a.100.exr
        # i.e., 'a.[96-100].exr m:[99]'
        #
        # The old a.99.exr got OVERWRITTEN, but not copied to a.97.exr!
        #
        # THIS IS an UNLIKELY OCCURANCE!
        #
        # However users should pay attention to the --showBadPadding option of 'lsseq'
        # and if need be, first fix SEQ with 'fixseqpadding' before using this
        # util to get correct results in all circumstances.
        #
        #  (*) Another example of badly padded frame numbers:
        #      02, 03, 04, ..., 0998, 0999, 1000, 1001, 
        #      This example should be two padded, not four padded,
        #      so 0998 and 0999 are badly padded frame numbers.
        #
        for i in frameList :
            origFile = seq[0] + currentSeparator + currentFormatStr.format(i) + '.' + seq[2]
            if os.path.exists(origFile) :
                origNames.append(origFile)
                newNames.append(seq[0] + newSeparator + newFormatStr.format(i+args.offsetFrames) \
                    + '.' + seq[2])

        if origNames == [] :
            if not args.silent :
                print(os.path.basename(sys.argv[0]), ": warning: ", arg,
                    " is nonexistent", file=sys.stderr, sep='')
            continue

        if not args.clobber :
            checkNames = [ x for x in newNames if x not in origNames ]

            f = ""
            for f in checkNames :
                if os.path.exists(f) :
                    abortSeq = True
                    break

            if abortSeq :
                if not args.silent :
                    print(os.path.basename(sys.argv[0]), ": warning: skipping ", arg,
                        ": renumbering would have overwritten a file outside the sequence being renumbered. e.g.: ",
                        f, file=sys.stderr, sep='')
                continue

        i = 0
        numFiles = len(origNames)
        fileRenamed = False
        while i < numFiles :
            #
            # Only rename files that have changed names.
            # This catches repadding of SEQ (i.e. no offset),
            # but some frames are already padded properly.
            #
            if origNames[i] != newNames[i] :
                fileRenamed = True
                if args.verbose :
                    print(origNames[i], " -> ", newNames[i], sep='')
                if not args.dryRun :
                    os.rename(origNames[i], newNames[i])
                    if touchFiles :
                        if touchTime == 0.0 :
                            os.utime(newNames[i])
                        else :
                            os.utime(newNames[i], (touchTime, touchTime))
            i += 1
        #
        # Continuation of above logic, printing warning if NO files in SEQ changed names.
        #
        if not fileRenamed and not args.silent :
            print(os.path.basename(sys.argv[0]),
                ": warning: no changes were made to ", arg, ": skipping",
                file=sys.stderr, sep='')

if __name__ == '__main__':
    main()
