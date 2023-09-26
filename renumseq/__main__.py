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
from datetime import datetime
import seqLister
from enum import Enum
import subprocess
import glob

# MAJOR version for incompatible API changes
# MINOR version for added functionality in a backwards compatible manner
# PATCH version for backwards compatible bug fixes
#
VERSION = "1.4.0"

PROG_NAME = "renumseq"

EXIT_NO_ERROR         = 0 # Clean exit.
EXIT_ERROR            = 1 # Internal error other than argparse - currently not used.
EXIT_ARGPARSE_ERROR   = 2 # The default code that argparse exits with if bad option.

# List of date formats accepted to set file times with --touch.
# They are same as the formats used by 'lsseq --onlyShow'.
#
# Note: We MUST list %y before %Y in each case below to make sure 
# that, for example, "200731" get's interpreted as July 31, 2020
# and not Mar 1, 2007, as it will if %Y is listed first because
# strptime() does not enforce zero padding for month, day, etc.
#
# Note the ordered pairs below. The second entry is the length
# of a properly zero padded date string, used to double check
# any matches that strptime() makes.
#
DATE_FORMAT_LIST = [
    ('%y%m%d', 6),
    ('%Y%m%d', 8),
    ('%y%m%d-%H', 9),
    ('%Y%m%d-%H', 11),
    ('%y%m%d-%H%M', 11),
    ('%Y%m%d-%H%M', 13),
    ('%y%m%d-%H%M%S', 13),
    ('%Y%m%d-%H%M%S', 15)
]

class Touch(Enum):
    CURRENT_TIME = 1
    ORIGINAL_TIME = 2
    SPECIFIC_TIME = 3

def warnSeqSyntax(silent, basename, seq) :
    if not silent :
        print( PROG_NAME,
            ": warning: invalid range [", seq, "] for seq ", basename,
            file=sys.stderr, sep='')

def main():

    NEVER_START_FRAME = -999999999999 # Seems safe enough.
    howToTouch = ""   # Set below.
    specificTime = 0  # Set below.
    currentTime = time.time()
    seqPath = '' # Used for --rename option, set early, also used later.

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
        prog=PROG_NAME,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent('''
            Renumber the frame range of each SEQ listed on the command line.
            SEQ should be specified using lsseq's native format.
            
            Protip: Turning off globbing, or enclosing SEQ in quotes, or placing
            backslashes ahead of '[' and ']' will likely be necessary to turn off the special
            treatment of '[' and ']' by the shell.

            Caution: The files in the sequence MUST BE correctly padded.
            Pay attention to lsseq's --showBadPadding for reports of badly padded frame
            numbers and fix them before renumbering a sequence with this utility.
            (This is a rare issue that can be fixed with the command 'fixSeqPadding'.)

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
    p.add_argument("--rename", type=str, nargs=1,
        dest="newSeqName",
        default=[],
        metavar="NEW_SEQNAME",
        help="Rename the DESCRIPTIVE_NAME part of SEQ from its existing name to NEW_SEQNAME. \
        When using this option then the command will exit with an error unless \
        exactly one SEQ is being renamed and/or renumbered.")
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
        metavar="[CC]YYMMDD[-hh[mm[ss]]]",
        help="If no date is provided then update the access time of \
        the files being renumbered to the current time. \
        Otherwise, use the date provided to update the \
        file's access time. (Default: renumbering a sequence leaves \
        the access time unchanged.) \
        When specifying the date, the optional CC (century) defaults to the current century. \
        The optional '-hh' (hours), 'mm' (minutes) or 'ss' (seconds) \
        default to zero if not specified. \
        Note: if this is the last argument on the command line and the optional \
        date was not specified then \
        append '--' before the list of SEQs to delineate the end of the options.")

    p.add_argument("--dryRun", "--dryrun", action="store_true",
        dest="dryRun", default=False,
        help="Don't renumber SEQ, just display how the \
        files would have been renumbered. Forces --verbose" )
    p.add_argument("--silent", "--quiet", "-s", action="store_true",
        dest="silent", default=False,
        help="suppress all errors and warnings")
    p.add_argument("--verbose", "-v", action="store_true",
        dest="verbose", default=False,
        help="list the mapping from old file-name to new file-name")

    p.add_argument("files", metavar="SEQ", nargs="*",
        help="image sequence in lsseq native format")

    args = p.parse_args()

    # The following regular expression is created to match lsseq native
    # sequence syntax which means (number below refer to parenthesis
    # groupings (**a**)):
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
    lsseqPattern = re.compile(r"(.+)([._])\[(-?[0-9]+-?-?[0-9]+)\]\.([a-zA-Z]+\.?[a-zA-Z]+[a-zA-Z0-9]*$)")

    # --rename has nargs set to "1", so parse_args() above will catch
    # most invalid cases. Now we need to catch four other invalid cases.
    #
    # 1) renumseq --rename aaa.[1-10].jpg
    # 2) renumseq --rename xxx aaa.[1-10].jpg bbb.[1-10].jpg
    # 3) renumseq --rename aaa.[1-10].jpg bbb.[1-10].jpg
    # 4) see below
    #
    # Case 1) is when the user likely forgot to put the NEW_SEQNAME 
    #         on the command-line when renaming 'aaa'.
    # Case 2) is when the user is trying to rename TWO sequences to
    #         the same name ('xxx') which is obviously undesirable.
    # Case 3) Hard to say what the user is doing here exactly, but
    #         they either forgot to add new NEW_SEQNAME *and* to
    #         remove one or other of the two SEQ from the command-line.
    #         *OR* they didn't want to actually use --rename at all.
    #         How to catch this one is if the NEW_SEQNAME
    #         looks like an SEQ in lsseq native-format.
    # Case 4) $ lsseq
    #         aaa.[1-10].jpg
    #         bbb.[0101-0110].jpg
    #         $ renumseq --start 20 --rename bbb aaa.[1-10].jpg
    #
    #         In this case, regardless of the start frame, or padding differences,
    #         seq 'aaa' is attempting to be renamed to an SEQ 'bbb' that already exists.
    #
    if len(args.newSeqName) == 1 :

        # One other case not mentioned above. --rename is assuming that the "newSeqName" is
        # just the "descriptiveName" part of the sequence, i.e no path (and no ".<framenum>.ext",
        # checked below), so check for a possibly embedded path.
        #
        if len(args.newSeqName[0].split('/')) > 1 :
            if not args.silent :
                print(PROG_NAME, ": error: --rename will rename the sequence in-place, so please omit the path ",
                    '/'.join(args.newSeqName[0].split('/')[:-1]),
                    file=sys.stderr, sep='')
            sys.exit(EXIT_ARGPARSE_ERROR)

        match = lsseqPattern.search(args.newSeqName[0])

        if len(args.files) == 0 and match : # If 'not match', command will just exit cleanly below.
            if not args.silent :
                print(PROG_NAME, ": error: NEW_SEQNAME not supplied. Perhaps NEW_SEQNAME was",
                    file=sys.stderr, sep='')
                print("                 omitted from '--rename ", args.newSeqName[0], "'", " by mistake?",
                    file=sys.stderr, sep='')
            sys.exit(EXIT_ARGPARSE_ERROR)

        elif len(args.files) >= 1 and match : # If len() > 1 then also invalid, but this catches both.
            if not args.silent :
                print(PROG_NAME, ": error: --rename NEW_SEQNAME should only supply the descriptive-name",
                    file=sys.stderr, sep='')
                print("                 part of the new name. That is, ", args.newSeqName[0],
                    file=sys.stderr, sep='')
                print("                 appears to be a full lsseq native-format description of a sequence.",
                    file=sys.stderr, sep='')
            sys.exit(EXIT_ARGPARSE_ERROR)

        elif len(args.files) > 1 :
            if not args.silent :
                print(PROG_NAME, ": error: can NOT rename more than one SEQ at a time.",
                    file=sys.stderr, sep='')
            sys.exit(EXIT_ARGPARSE_ERROR)

        # Now check to see if a sequence with NEW_SEQNAME exists already.
        # This code relies on lsseq >= v2.5.0 be installed.
        #
        elif len(args.files) == 1 :
            seqPath = '/'.join(args.files[0].split('/')[:-1])
            if len(seqPath) > 0 :
                seqPath = seqPath + '/'

            # This next globPattern will put us in the ballpark - lsseq will check more carefully
            # based on this. If NEW_SEQNAME contains a '*', '?', '[' or ']', then this isn't going
            # to work so well, so hopefully the user isn't trying to rename to something with
            # a globbing-wildcard as part of the new name.
            #
            globPattern = seqPath + args.newSeqName[0] + '[._]' + '[0-9]*.*'

            globResult = glob.glob(globPattern)

            if len(globResult) > 0 :
                lsseqCmd = ['lsseq', '--looseNumSeparator', '--onlySequences', '--noErrorLists'] + globResult
                lsseqResult = subprocess.run(lsseqCmd, capture_output=True, text=True)
                if len(lsseqResult.stdout) > 0 :
                    if not args.silent :
                        print(PROG_NAME, ": error: can NOT rename to an existing sequence ",
                            lsseqResult.stdout,
                            file=sys.stderr, sep='', end='')
                    sys.exit(EXIT_ARGPARSE_ERROR)

    if len(args.files) == 0 :
        sys.exit(EXIT_NO_ERROR)

    # The following logic means "do nothing" - so just exit cleanly (**b**)
    #
    if args.offsetFrames == 0 \
            and args.pad < 0 \
            and not args.fixUnderscore \
            and args.startFrame == NEVER_START_FRAME \
            and len(args.newSeqName) == 0 :
        if not args.silent :
            print(PROG_NAME,
                ": warning: no offset, no rename, no padding change, etc., nothing to do",
                file=sys.stderr, sep='')
        sys.exit(EXIT_NO_ERROR)

    # args.touch is either a string, presumably containing a date (so need to
    # check its validity), the string "0" (meaning --touch was called with NO argument),
    # or None, meaning --touch was not invoked on the command line.
    # 
    if args.touch == None : # --touch NOT called
        howToTouch = Touch.ORIGINAL_TIME

    elif args.touch == "0" : # Touch with current time.
        howToTouch = Touch.CURRENT_TIME

    else : # Touch with time specified on the command line.
        howToTouch = Touch.SPECIFIC_TIME

        # Loop through list of acceptable formats declared globally.
        #
        matchedDate = False
        for dateFormat in DATE_FORMAT_LIST :
            try: 
                timeData = datetime.strptime(args.touch, dateFormat[0])

                # Make sure the prior strptime() call matched against a string
                # with zero padding for month, day, etc. If the length of the matched
                # string doesn't add up to what it should be if zero padded
                # then reject the match and keep looping.
                # 
                # This test is needed since strptime() does not ENFORCE zero
                # padding of months, days, minutes etc. leading to possible
                # ambiguity and thus is an undesireable feature of strptime().
                #
                # This code works around that limitation.
                #
                if len(args.touch) == dateFormat[1] :
                    matchedDate = True
                    break

            except ValueError as ve:
                # Note, we could probably make clever use of the ValueError
                # reported here, but since we have a list of possible formats
                # sorting it out if everthing fails seems like more trouble
                # than it's worth.
                #
                continue

        if not matchedDate :
            if not args.silent :
                print(PROG_NAME,
                    ": error: argument --touch: the time must be of the form [CC]YYMMDD[-hh[mm[ss]]]",
                    file=sys.stderr, sep='')
            sys.exit(EXIT_ARGPARSE_ERROR)

        specificTime = int(time.mktime(timeData.timetuple())) # Epoch time

    if args.dryRun : # verbose to show how renumbering would occur.
        args.verbose = True

    for arg in args.files :
        abortSeq = False

        # Check if 'arg' is a sequence in valid lsseq native format
        #
        match = lsseqPattern.search(arg)
        if not match :
            if not args.silent :
                print(PROG_NAME, ": warning: ", arg,
                    " not a sequence or not in lsseq native format",
                    file=sys.stderr, sep='')
            continue

        v = match.groups()

        usesUnderscore = (v[1] == '_')
        seq = [v[0], v[2], v[3]] # base filename, range, file-extension. (see above (**a**))

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

            # This duplicates the test above (**b**) because now
            # we might have a zero offset for this sequence.
            # Instead of exiting we just skip to the next seq.
            #
            if args.offsetFrames == 0 \
                    and args.pad < 0 \
                    and not args.fixUnderscore :
                if not args.silent :
                    print(PROG_NAME,
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

        origName = []
        newName = []
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
                origName.append(origFile)
                if len(args.newSeqName) == 1 :
                    newName.append(seqPath + args.newSeqName[0] + newSeparator + \
                        newFormatStr.format(i+args.offsetFrames) \
                        + '.' + seq[2])
                else :
                    newName.append(seq[0] + newSeparator + \
                        newFormatStr.format(i+args.offsetFrames) \
                        + '.' + seq[2])

        if origName == [] :
            if not args.silent :
                print(PROG_NAME, ": warning: ", arg,
                    " is nonexistent", file=sys.stderr, sep='')
            continue

        if not args.clobber :
            checkNames = [ x for x in newName if x not in origName ]

            f = ""
            for f in checkNames :
                if os.path.exists(f) :
                    abortSeq = True
                    break

            if abortSeq :
                if not args.silent :
                    print(PROG_NAME, ": warning: skipping ", arg,
                        ": renumbering would have overwritten a file outside the sequence being renumbered. e.g.: ",
                        f, file=sys.stderr, sep='')
                continue

        i = 0
        numFiles = len(origName)
        fileRenamed = False
        while i < numFiles :
            #
            # Only rename files that have changed names.
            # This catches repadding of SEQ (i.e. no offset),
            # but some frames are already padded properly.
            #
            if origName[i] != newName[i] :
                fileRenamed = True
                if args.verbose :
                    print(origName[i], " -> ", newName[i], sep='')
                if not args.dryRun :
                    stat = os.stat(origName[i])
                    os.rename(origName[i], newName[i])
                    if howToTouch == Touch.CURRENT_TIME :
                        os.utime(newName[i], (currentTime, currentTime))
                    elif howToTouch == Touch.SPECIFIC_TIME :
                        os.utime(newName[i], (specificTime, specificTime))
                    else :
                        os.utime(newName[i], (stat.st_atime, stat.st_mtime))
            i += 1
        #
        # Continuation of above logic, printing warning if NO files in SEQ changed names.
        #
        if not fileRenamed and not args.silent :
            print(PROG_NAME,
                ": warning: no changes were made to ", arg, ": skipping",
                file=sys.stderr, sep='')

if __name__ == '__main__':
    main()
