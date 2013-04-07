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
import struct
import hashlib
import logging


def mp3hash(path, alg='sha1', maxbytes=None):
    """Returns the hash of the sound contents of a ID3 tagged file
    Convenience function which wraps TaggedFile
    Returns None on failure
    """
    if maxbytes is not None and maxbytes <= 0:
        raise ValueError('maxbytes should be a positive integer')

    if os.path.isfile(path):
        with open(path, 'rb') as ofile:
            return TaggedFile(ofile).hash(maxbytes=maxbytes)


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
    blocksize = 2 ** 19                # block size 512 KiB
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


def memento(function):
    def wrapper(self):
        attr_name = '_' + function.func_name + '_value'
        if not hasattr(self, attr_name):
            setattr(self, attr_name, function(self))
        return getattr(self, attr_name)
    return wrapper


def parse_7bitint(bytes, bits=7, mask=128 - 1):
    """ Parses a big endian integer from a list of bytes
    taking only the first 7 bits from each byte

    mask: 0111 1111 (removes 8th bit)
    shift: offset to reorder bytes as if the 8th didn't exist
    the bytes are walked in reverse order, as it is in big endian

    This is because ID3v2 uses 'sync safe integers'
    which always have its mrb zeroed
    """
    return sum(
        (bytes[-i - 1] & mask) << shift
        for i, shift in
        enumerate(xrange(0, len(bytes) * bits, bits))
    )


class TaggedFile(object):

    def __init__(self, file):
        self.file = file
        self.filesize = os.fstat(file.fileno()).st_size

    @property
    @memento
    def has_id3v1(self):
        "Returns True if the file is id3v1 tagged"
        if self.filesize < 128:  # at least 128 bytes are needed
            return False

        self.file.seek(-128, 2)
        return self.file.read(3) == 'TAG'

    @property
    @memento
    def has_id3v1ext(self):
        "Returns True if the file is id3v1 with extended tag"
        if self.filesize < 128 + 227:
            return False

        self.file.seek(-(227 + 128), 2)  # 227 before regular tag
        return self.file.read(4) == 'TAG+'

    @property
    @memento
    def id3v1ext_size(self):
        "Returns the size of the extended tag if exists"
        if self.has_id3v1ext:
            return 227
        return 0

    @property
    @memento
    def id3v1_size(self):
        "Returns the size in bytes of the id3v1 tag"
        if self.has_id3v1:
            return 128
        return 0

    @property
    @memento
    def id3v1_totalsize(self):
        "Returns the size in bytes of the id3v1 tag"
        return self.id3v1_size + self.id3v1ext_size

    @property
    @memento
    def has_id3v2(self):
        "Returns True if the file is id3v2 tagged"
        if self.filesize < 10:  # 10 bytes at least for the header
            return False

        self.file.seek(0)
        return self.file.read(3) == 'ID3'

    @property
    @memento
    def has_id3v2ext(self):
        "Returns True if the file has id3v2 extended header"
        if self.filesize < self.id3v2_size:
            return False

        self.file.seek(5)  # jump header
        flags, = struct.unpack('>b', self.file.read(1))
        return bool(flags & 0x40)  # xAx0 0000 get A from byte

    @property
    @memento
    def id3v2_size(self):
        """ Returns the size in bytes of the id3v2 tag
        id3v2 header is 10 bytes long which starts with ID3:
            0 I
            1 D
            2 3
            3 Version number
            4 Version revision
            5 Flags
            6 Size 4 7bit bytes big endian
            7
            8
            9
        """
        if not self.has_id3v2:
            return 0

        self.file.seek(6)
        # id3v2 size big endian 7bit 4 bytes
        size_byte_string, = struct.unpack('>4s', self.file.read(4))
        size = parse_7bitint([ord(i) for i in size_byte_string])

        return size + 10  # header size not included

    @property
    @memento
    def id3v2ext_size(self):
        "Returns the size in bytes of the id3v2 extended tag"
        if not self.has_id3v2 or not self.has_id3v2ext:
            return 0

        self.file.seek(self.id3v2_size)
        size_byte_string, = struct.unpack('>i', self.file.read(4))
        size = parse_7bitint([ord(i) for i in size_byte_string])

        flags, = struct.unpack('>bb', self.file.read(2))
        crc = 4 if flags & 8 else 0  # flags are A000 get A

        padding_byte_string, = struct.upnack('>i', self.file.read(4))
        padding = parse_7bitint([ord(i) for i in padding_byte_string])

        return size + crc + padding + 10  # header size not included

    @property
    @memento
    def id3v2_totalsize(self):
        "Returns the total size of the id3v2 tag"
        return self.id3v2_size + self.id3v2ext_size

    @property
    @memento
    def startbyte(self):
        "Returns the starting byte position of music data in the file"
        return self.id3v2_totalsize

    @property
    @memento
    def endbyte(self):
        "Returns the last byte position of music data in the file"
        self.file.seek(-self.id3v1_totalsize, 2)
        return self.file.tell()

    @property
    @memento
    def musiclimits(self):
        "Returns the (start, end) for music in the file"
        return (self.startbyte, self.endbyte)

    @property
    @memento
    def music_size(self):
        "Returns the total count of music data bytes in the file"
        return self.filesize - self.id3v1_totalsize - self.id3v2_totalsize

    def hash(self, alg='sha1', maxbytes=None):
        """Returns the hash for a certain audio file ignoring tags
        Non cached function. Calculates the hash each time it's called
        """
        try:
            start, end = self.musiclimits
        except IOError, ioerr:
            logging.error('While parsing tags: {}'.format(ioerr))
            return
        else:
            return hashfile(self.file, start, end, alg, maxbytes)
