#!/usr/bin/env python
#-*- coding: utf-8 -*-
"""
Hashes audio files ignoring metadata

id3v1 is 128 bytes at the end of the file starting with 'TAG'
id3v1 extended is 227 bytes before regular id3v1 tag starting with 'TAG+'
total size: 128 + (227 if extended)

id3v2 has a 10 bytes header at the begining of the file.
      byte 5 holds flags. 6th bit indicates extended tag
      bytes 6-10 are the tag size (not counting header)
id3v2 extended has a 10 bytes header after the regular id3v2
      bytes 1-4 are the tag size (not counting header nor padding)
      bytes 4-6 holds some flags. Leftmost bit indicates CRC presence
      bytes 6-10 are the tag padding size (extra blank size within tag)
total size: 10 + tagsize + (10 + etagsize + padding if extended)

Based on id3v1 wikipedia docs: http://en.wikipedia.org/wiki/ID3
Based on id3v2 docs: http://www.id3.org/id3v2.3.0

Javier Santacruz 2012-06-03
"""

import os
import sys
import struct
import hashlib
import logging
from optparse import OptionParser

_LOGGING_FMT_ = '%(asctime)s %(levelname)-8s %(message)s'


def error(msg, is_exit=True):
    logging.error(msg)
    if is_exit:
        sys.exit()


def hashfile(ofile, start, end, alg='sha1', maxbytes=None):
    """Hashes a open file data starting from byte 'start' to the byte 'end'
    max is the maximun amount of data to hash, in bytes.
    The hexdigest string is calculated considering only bytes between start,end
    """
    if maxbytes:
        end = min(end, start + maxbytes)

    hasher = hashlib.new(alg)
    ofile.seek(start)

    size = end - start                 # total size in bytes to hash
    blocksize = 524288                 # block size 512 KiB
    nblocks = size // blocksize        # n full blocks
    firstblocksize = size % blocksize  # spare data, not enough for a block

    logging.debug("Start: {0} End: {1} Size: {2}".format(start, end, size))

    block = ''
    try:
        if firstblocksize > 0:
            block = ofile.read(firstblocksize)
            hasher.update(block)

        for i in xrange(nblocks):
            hasher.update(block)
            block = ofile.read(blocksize)
    finally:
        ofile.close()

    return hasher.hexdigest()


class TaggedFile(object):

    attrs = ('has_id3v1', 'has_id3v1ext', 'id3v1_size', 'id3v1ext_size',
             'id3v1_totalsize', 'has_id3v2', 'has_id3v2ext', 'id3v2_size',
             'id3v2ext_size', 'id3v2_totalsize', 'startbyte', 'endbyte',
             'musiclimits')

    def __init__(self, path):
        self.path = path
        self.filesize = os.path.getsize(self.path)
        self.taginfo = None
        self.file = None

    def __getattribute__(self, key):
        """Returns cached version for properties listed in self.attrs
        Lazy initialize self.taginfo when accesing any property the first time
        Avoids calling self.attrs properties with self.file being None
        """
        if key in object.__getattribute__(self, 'attrs'):
            if self.taginfo is None:
                self.__getinfo()
            return self.taginfo[key]

        return object.__getattribute__(self, key)

    def __getinfo(self):
        """Calculates and returns taginfo dict
        taginfo dict caches TaggedFile info
        """
        self.file = open(self.path, 'rb')
        # taginfo = {'has_id3v1': None, ..
        self.taginfo = dict(zip(self.attrs, (None,) * len(self.attrs)))

        for attr in self.attrs:
            self.taginfo[attr] = object.__getattribute__(self, attr)

        logging.debug("taginfo: {0} {1}"
                      .format(os.path.basename(self.path), self.taginfo))

        self.file.close()
        self.file = None
        return self.taginfo

    @property
    def has_id3v1(self):
        "Returns True if the file is id3v1 tagged"
        if self.filesize < 128:  # at least 128 bytes are needed
            return False

        self.file.seek(-128, 2)
        return self.file.read(3) == 'TAG'

    @property
    def has_id3v1ext(self):
        "Returns True if the file is id3v1 with extended tag"
        if self.filesize < 128 + 227:
            return False

        self.file.seek(-(227 + 128), 2)  # 227 before regular tag
        return self.file.read(4) == 'TAG+'

    @property
    def id3v1ext_size(self):
        "Returns the size of the extended tag if exists"
        if self.has_id3v1ext:
            return 227
        return 0

    @property
    def id3v1_size(self):
        "Returns the size in bytes of the id3v1 tag"
        if self.has_id3v1:
            return 128
        return 0

    @property
    def id3v1_totalsize(self):
        "Returns the size in bytes of the id3v1 tag"
        return self.id3v1_size + self.id3v1ext_size

    @property
    def has_id3v2(self):
        "Returns True if the file is id3v2 tagged"
        if self.filesize < 10:  # 10 bytes at least for the header
            return False

        self.file.seek(0)
        return self.file.read(3) == 'ID3'

    @property
    def has_id3v2ext(self):
        "Returns True if the file has id3v2 extended header"
        if self.filesize < self.id3v2_size:
            return False

        self.file.seek(5)
        flags, = struct.unpack('>b', self.file.read(1))
        return bool(flags & 0x40)  # xAx0 0000 get A from byte

    @property
    def id3v2_size(self):
        "Returns the size in bytes of the id3v2 tag"
        if not self.has_id3v2:
            return 0

        self.file.seek(6)
        # id3v2 size big endian 4 bytes
        size, = struct.unpack('>i', self.file.read(4))
        size += 10  # header itself
        return size

    @property
    def id3v2ext_size(self):
        "Returns the size in bytes of the id3v2 extended tag"
        if not self.has_id3v2 or not self.has_id3v2ext:
            return 0

        self.file.seek(self.id3v2_size)
        size = struct.unpack('>i', self.file.read(4))
        flags, = struct.unpack('>bb', self.file.read(2))
        crc = 4 if flags & 8 else 0  # flags are A000 get A
        padding = struct.upnack('>i', self.file.read(4))
        return size + crc + padding + 10

    @property
    def id3v2_totalsize(self):
        "Returns the total size of the id3v2 tag"
        return self.id3v2_size + self.id3v2ext_size

    @property
    def startbyte(self):
        "Returns the byte where the music starts in file"
        return self.id3v2_totalsize

    @property
    def endbyte(self):
        "Returns the last byte of music data in file"
        self.file.seek(-self.id3v1_totalsize, 2)
        return self.file.tell()

    @property
    def musiclimits(self):
        "Returns the (start, end) for music in file"
        return (self.startbyte, self.endbyte)

    @property
    def music_size(self):
        "Returns the total count of bytes of music in file"
        return self.filesize - self.id3v1_totalsize - self.id3v2_totalsize

    def hash(self, alg='sha1', maxbytes=None):
        """Returns the hash for a certain audio file ignoring tags
        Non cached function. Calculates the hash each time it's called
        """
        with open(self.path, 'rb') as ofile:
            try:
                start, end = self.musiclimits
            except IOError, ioerr:
                logging.error('While parsing tags for {0}: {1}'\
                              .format(self.path, ioerr))
                return
            else:
                return hashfile(ofile, start, end, alg, maxbytes)


def mp3hash(path, alg='sha1', maxbytes=None):
    """Returns the hash of the sound contents of a ID3 tagged file
    Convenience function which wraps TaggedFile
    Returns None on failure
    """
    if maxbytes is not None and maxbytes <= 0:
        raise ValueError('maxbytes should be a positive integer')

    if os.path.isfile(path):
        return TaggedFile(path).hash(maxbytes=maxbytes)


def list_algorithms():
    for alg in hashlib.algorithms:
        print alg


def main():
    "Main program"

    if opts.list_algorithms:
        list_algorithms()
        sys.exit(0)

    if opts.algorithm not in hashlib.algorithms:
        error("Unkown '{0}' algorithm. Available options are: {1}"\
              .format(opts.algorithm, ", ".join(hashlib.algorithms)))

    for arg in args:
        path = os.path.realpath(arg)
        if not os.path.isfile(path):
            error("Couldn't open {0}. File doesn't exist or isn't a"
                          " regular file".format(arg))
            continue

        tagfile = TaggedFile(path)
        print tagfile.hash(opts.algorithm),  # No \n
        print os.path.basename(path) if not opts.hash else ''


if __name__ == "__main__":
    parser = OptionParser()

    parser.add_option("-a", "--algorithm", dest="algorithm", action="store",
                      default='sha1', help="Hash algorithm to use. "
                      "Default sha1.  See --list-algorithms")

    parser.add_option("-l", "--list-algorithms", dest="list_algorithms",
                      action="store_true", default=False,
                      help="List available algorithms")

    parser.add_option("-q", "--hash", dest="hash", action="store_true",
                      default=False, help="Print only hash information, no "
                      "filename")

    parser.add_option("-m", "--maxbytes", dest="maxbytes", action="store",
                      default=None, help="Max number of bytes of music to hash")

    parser.add_option("-o", "--output", dest="output", action="store",
                      default=False, help="Redirect output to a file")

    parser.add_option("-v", "--verbose", dest="verbose", action="count",
                      default=0, help="")

    parser.set_usage("Usage: [options] FILE [FILE ..]")

    (opts, args) = parser.parse_args()

    # Configure logging
    logging_levels = {0: logging.WARNING, 1: logging.INFO, 2: logging.DEBUG}
    level = logging_levels[opts.verbose if opts.verbose < 3 else 2]
    logging.basicConfig(level=level, format=_LOGGING_FMT_)

    if opts.output:
        stdout = sys.stdout
        try:
            sys.stdout = open(opts.output, 'w')
        except IOError, err:
            sys.stdout = stdout
            error("Couldn't open {0}: {1}".format(sys.stdout, err))

    if not args and not opts.list_algorithms:
        parser.print_help()
        print
        error("Insufficient arguments")

    if opts.maxbytes is not None and opts.maxbytes <= 0:
        parser.print_help()
        print
        error("Invalid value for --maxbytes it should be a positive integer")

    main()
