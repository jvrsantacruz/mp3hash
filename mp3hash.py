#-*- coding: utf-8 -*-
"""
Hashes audio files ignoring metadata

The following metadata standards are supported:

    id3v1, id3v1 extended, id3v2.2, id3v2.3 and id3v.24

The main components are the mp3hash function and the TaggedFile class.

* mp3hash will compute the hash on the music (and only the music)
  of the file in the given path.

* TaggedFile class takes a file-like object supporting
  seek and negative values for seek and will parse all the sizes
  for the metadata stored within it.

Technical details:
~~~~~~~~~~~~~~~~~~

id3v1 is 128 bytes at the end of the file starting with 'TAG'
id3v1 extended is 227 bytes before regular id3v1 tag starting with 'TAG+'

total size: 128 + (227 if extended)

id3v2 has a 10 bytes header at the begining of the file.
      byte 5 holds flags. 4th bit indicates presence of footer in v2.4
      bytes 6-10 are the tag size (not counting header)

total size: header + tagsize + footer (if any)

Based on id3v1 wikipedia docs: http://en.wikipedia.org/wiki/ID3
Based on id3v2 docs: http://www.id3.org/id3v2.3.0

Javier Santacruz 2012-06-03
"""

import struct
import hashlib
import logging
from itertools import repeat


def mp3hash(path, maxbytes=None, hasher=None):
    """Returns the hash of the sound contents of a ID3 tagged file
    Convenience function which wraps TaggedFile
    Returns None on failure
    """
    if maxbytes is not None and maxbytes <= 0:
        raise ValueError(u'maxbytes must be a positive integer')

    if hasher is None:
        hasher = hashlib.new('sha1')

    with open(path, 'rb') as ofile:
        return TaggedFile(ofile).hash(maxbytes=maxbytes, hasher=hasher)


def hashfile(file, start, end, hasher, maxbytes=None, blocksize=2 ** 19):
    """Hashes an open file data starting from byte 'start' to the byte 'end'
    max is the maximun amount of data to hash, in bytes.
    The hexdigest string is calculated considering only bytes between start,end
    default block size is 512 KiB
    """
    if maxbytes is not None and maxbytes > 0:
        end = min(end, start + maxbytes)

    file.seek(start)

    size = end - start                 # total size in bytes to hash
    nblocks = size // blocksize        # n full blocks
    last_blocksize = size % blocksize  # spare data, not enough for a block

    for read in repeat(file.read, nblocks):
        block = read(blocksize)
        hasher.update(block)

    if last_blocksize:
        block = file.read(last_blocksize)
        hasher.update(block)

    return hasher.hexdigest()


def memento(function):
    def wrapper(self):
        attr_name = '_' + function.__name__ + '_value'
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

    > The tag size is encoded with four bytes where the most
    significant bit (bit 7) is set to zero in every byte, making a total
    of 28 bits. The zeroed bits are ignored, so a 257 bytes long tag is
    represented as $00 00 02 01.
    """
    return sum(
        (bytes[-i - 1] & mask) << shift
        for i, shift in
        enumerate(range(0, len(bytes) * bits, bits))
    )


ID3V1_SIZE = 128
ID3V1_EXTENDED_SIZE = ID3V1_SIZE + 227

ID3V2_HEADER_SIZE = 10
ID3V2_FOOTER_SIZE = 10


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

            ID3v2/file identifier      "ID3"
            ID3v2 version              $03 00
            ID3v2 flags                %abcd0000
            ID3v2 size             4 * %0xxxxxxx

        Flags:  The b (6th) bit indicates whether or not the header is
                followed by an extended header. (mask is 0x40)

        (v2.4)  The d (4th) bit indicates that a footer  is present at the
                end of the tag. (mask is 0x10)
        """
        self.file.seek(0)
        header = self.file.read(ID3V2_HEADER_SIZE)

        id3, v, r, flags, size = struct.unpack('>3sBBB4s', header)

        if isinstance(size, str):  # python3's unpack returns bytes
            size = [ord(i) for i in size]

        return id3, v, r, flags, parse_7bitint(size)

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
        """ Returns the size in bytes of the whole id3v2 tag

        > The ID3v2 tag size is the size of the complete tag after
        unsychronisation, including padding, excluding the header but not
        excluding the extended header.
        """
        if not self.has_id3v2:
            return 0

        id3, ver, rev, flags, size = self._id3v2_header

        # id3v2.4 also includes an optional 10 bytes footer
        if ver == 4 and flags & 0x10:
            size += ID3V2_FOOTER_SIZE

        return ID3V2_HEADER_SIZE + size

    id3v2_totalsize = id3v2_size

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

    def hash(self, hasher, maxbytes=None):
        """Returns the hash for a certain audio file ignoring tags """
        try:
            start, end = self.musiclimits
        except IOError as ioerr:
            logging.error(u'While parsing tags: {0}'.format(ioerr))
        else:
            return hashfile(self.file, start, end, hasher, maxbytes)
