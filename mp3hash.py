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

import struct
import hashlib
import logging


def mp3hash(path, alg='sha1', maxbytes=None):
    """Returns the hash of the sound contents of a ID3 tagged file
    Convenience function which wraps TaggedFile
    Returns None on failure
    """
    if maxbytes is not None and maxbytes <= 0:
        raise ValueError(u'maxbytes must be a positive integer')

    with open(path, 'rb') as ofile:
        return TaggedFile(ofile).hash(maxbytes=maxbytes)


def hashfile(ofile, start, end, alg='sha1', maxbytes=None):
    """Hashes an open file data starting from byte 'start' to the byte 'end'
    max is the maximun amount of data to hash, in bytes.
    The hexdigest string is calculated considering only bytes between start,end
    """
    if maxbytes > 0:
        end = min(end, start + maxbytes)

    hasher = hashlib.new(alg)
    ofile.seek(start)

    size = end - start                 # total size in bytes to hash
    blocksize = 2 ** 19                # block size 512 KiB
    nblocks = size // blocksize        # n full blocks
    firstblocksize = size % blocksize  # spare data, not enough for a block

    logging.debug(u"Start: {0} End: {1} Size: {2}".format(start, end, size))

    block = ''
    if firstblocksize > 0:
        block = ofile.read(firstblocksize)
        hasher.update(block)

    for i in xrange(nblocks):
        hasher.update(block)
        block = ofile.read(blocksize)

    return hasher.hexdigest()


def memento(function):
    def wrapper(self):
        attr_name = '_' + function.func_name + '_value'
        if not hasattr(self, attr_name):
            setattr(self, attr_name, function(self))
        return getattr(self, attr_name)
    return wrapper


def parse_7bitint(bytes, bits=7, mask=(1 << 7) - 1):
    """ Parses a big endian integer from a list of bytes
    taking only the first 7 bits from each byte

    Do not set bits and mask parameters.

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


ID3V1_SIZE = 128
ID3V1_EXTENDED_SIZE = ID3V1_SIZE + 227

ID3V2_HEADER_SIZE = 10
ID3V2_EXTENDED_HEADER_SIZE = 10


class TaggedFile(object):

    def __init__(self, file):
        self.file = file
        self.file.seek(0, 2)  # end of file
        self.filesize = self.file.tell()

    @property
    @memento
    def has_id3v1(self):
        "Returns True if the file is id3v1 tagged"
        if self.filesize < ID3V1_SIZE:
            return False

        self.file.seek(-ID3V1_SIZE, 2)  # last bytes of file
        return self.file.read(3) == 'TAG'

    @property
    @memento
    def has_id3v1ext(self):
        "Returns True if the file is id3v1 with extended tag"
        if self.filesize < ID3V1_EXTENDED_SIZE:
            return False

        self.file.seek(-ID3V1_EXTENDED_SIZE, 2)  # 227 before regular tag
        return self.file.read(4) == 'TAG+'

    @property
    @memento
    def id3v1ext_size(self):
        "Returns the size of the extended tag if exists"
        return ID3V1_EXTENDED_SIZE if self.has_id3v1ext else 0

    @property
    @memento
    def id3v1_size(self):
        "Returns the size in bytes of the id3v1 tag"
        return ID3V1_SIZE if self.has_id3v1 else 0

    @property
    @memento
    def id3v1_totalsize(self):
        "Returns the size in bytes of the id3v1 tag"
        return self.id3v1_size + self.id3v1ext_size

    @property
    @memento
    def _id3v2_header(self):
        """Returns id3v2 header: (id3, version, revision, flags, size)

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
        self.file.seek(0)
        header = self.file.read(ID3V2_HEADER_SIZE)

        id3, v, r, flags, size = struct.unpack('>3sBBB4s', header)

        return id3, v, r, flags, parse_7bitint(map(ord, size))

    @property
    @memento
    def has_id3v2(self):
        "Returns True if the file is id3v2 tagged"
        if self.filesize < ID3V2_HEADER_SIZE:
            return False

        id3, ver, rev, flags, size = self._id3v2_header
        return id3 == 'ID3'

    @property
    @memento
    def id3v2_size(self):
        " Returns the size in bytes of the whole id3v2 tag"
        if not self.has_id3v2:
            return 0

        id3, ver, rev, flags, size = self._id3v2_header
        return size + ID3V2_HEADER_SIZE

    @property
    @memento
    def _id3v2ext_header(self):
        """Returns id3v2 extended header: (size, flags, padding)

        id3v2 extended header is found inmediately after the id3v2 tags
        its 10 bytes long:
            0 Size 4 7bit bytes big endian
            1
            2
            3
            4 Flags1
            5 Flags0
            6 Padding 4 7bit bytes big endian
            7
            8
            9
        """
        self.file.seek(self.id3v2_size)
        header = self.file.reader(ID3V2_EXTENDED_HEADER_SIZE)

        size, flags, padding = struct.unpack('>4sBB4s', header)

        return (parse_7bitint(map(ord, size)),
                flags,
                parse_7bitint(map(ord, padding)))

    @property
    @memento
    def has_id3v2ext(self):
        "Returns True if the file has id3v2 extended header"
        if self.filesize < self.id3v2_size:
            return False

        id3, ver, rev, flags, size = self._id3v2_header
        return bool(flags & 0x40)  # xAx0 0000 get A from byte

    @property
    @memento
    def id3v2ext_size(self):
        "Returns the size in bytes of the id3v2 extended tag"
        if not self.has_id3v2 or not self.has_id3v2ext:
            return 0

        size, flags, padding_size = self._id3v2ext_header
        crc_size = 4 if flags & 0x08 else 0  # flags are A000, get A

        return size + crc_size + padding_size + ID3V2_EXTENDED_HEADER_SIZE

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
            logging.error(u'While parsing tags: {}'.format(ioerr))
            return
        else:
            return hashfile(self.file, start, end, alg, maxbytes)
