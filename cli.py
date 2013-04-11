#!/usr/bin/env python
#-*- coding: utf-8 -*-

import os
import sys
import hashlib
from optparse import OptionParser

from mp3hash import mp3hash


# hashlib.algorithms was included in python 2.7
ALGORITHMS = getattr(
    hashlib,
    'algorithms',
    ('md5', 'sha1', 'sha224', 'sha256', 'sha384', 'sha512')
)


def error(msg, code=1):
    print(msg)
    sys.exit(code)


def list_algorithms():
    print(u'\n'.join(ALGORITHMS))


def main():
    opts, args, parser = parse_arguments()

    if not args and not opts.list_algorithms:
        parser.print_help()
        error(u"\nInsufficient arguments", code=2)

    if opts.maxbytes is not None and opts.maxbytes <= 0:
        parser.print_help()
        print()
        error(u"\nInvalid value for --maxbytes it should be a positive integer")

    if opts.list_algorithms:
        list_algorithms()
        sys.exit()

    if opts.algorithm not in ALGORITHMS:
        error(u"Unkown '{}' algorithm. Available options are: {}"
              .format(opts.algorithm, ", ".join(ALGORITHMS)), code=2)

    for arg in args:
        path = os.path.realpath(arg)
        if not os.path.isfile(path):
            error(u"File at '{}' does not exist or it is not a regular file"
                  .format(arg))
            continue

        hasher = hashlib.new(opts.algorithm)

        print(u'{hash} {filename}'.format(
            hash=mp3hash(path, maxbytes=opts.maxbytes, hasher=hasher),
            filename=os.path.basename(path) if not opts.hash else ''
        ))


def parse_arguments():
    parser = OptionParser()

    parser.add_option("-a", "--algorithm", default='sha1',
                      help="Hash algorithm to use. Default sha1.  "
                      "See --list-algorithms")

    parser.add_option("-l", "--list-algorithms", action="store_true",
                      default=False, help="List available algorithms")

    parser.add_option("-q", "--hash", action="store_true", default=False,
                      help="Print only hash information, no filename")

    parser.add_option("-m", "--maxbytes", type=int, default=None,
                      help="Max number of bytes of music to hash")

    parser.add_option("-o", "--output", default=False,
                      help="Redirect output to a file")

    parser.set_usage("Usage: [options] FILE [FILE ..]")

    (opts, args) = parser.parse_args()

    return opts, args, parser


def configure_output(output):
    if output:
        stdout = sys.stdout
        try:
            sys.stdout = open(output, 'w')
        except IOError as err:
            sys.stdout = stdout
            error(u"Couldn't open {}: {}".format(output, err))


if __name__ == "__main__":
    main()
