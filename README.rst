mp3hash
=======

Hashes music files ignoring meta-data.

Useful to detect the same song in different tagged files.

Use
===

Similarly to ``sha1sum`` or ``md5sum``, it takes one or more files and
returns the hashes, in this way:

::

    $ ./mp3hash  *.mp3
    6611bc5b01a2fc6a6386a871e8c51f86e1f12b33 13_Hotel-California-(Gipsy-Kings).mp3
    6611bc5b01a2fc6a6386a871e8c51f86e1f12b33 14_Hotel-California-(Gipsy-Kings).mp3

It returns the same hash number, even though the tags are different, and
so their regular hashes:

::

    $ sha1sum *.mp3
    6a1d5f8317add10e205ae30174630b47645fb5b4  13_Hotel-California-(Gipsy-Kings).mp3
    c28d6976114d31df3366d9935eb0bedd36cf1f0b  14_Hotel-California-(Gipsy-Kings).mp3

The hash it's made strictly using the music data in the file, by
calculating the tags sizes and omitting them.

The default hashing algorithm is ``sha-1``, but any algorithm can be
used as long it's supported by the Python's ``hashlib`` module. A
complete list of all available hashing algorithms can be obtained by
calling the program with the ``--list-algorithms``.

::

    $ ./mp3hash --list-algorithms
    md5
    sha1
    sha224
    sha256
    sha384
    sha512

    ./mp3hash --algorithm md5
    ac0fdd89454528d3fbdb19942a2e6653 13_Hotel-California-(Gipsy-Kings).mp3
    ac0fdd89454528d3fbdb19942a2e6653 14_Hotel-California-(Gipsy-Kings).mp3

Install
=======

It doesn't have any dependences besides ``python2.6+`` so you should be
able to run the script straight.

Technical details
=================

Supported and ignored meta-data tags are: id3v1, id3v2 both in their
simple and indexed forms

About id3v1
-----------

-  id3v1 is 128 bytes at the end of the file starting with 'TAG'
-  id3v1 extended is 227 bytes before regular id3v1 tag starting with
   'TAG+'

total size: 128 + (227 if extended)

About id3v2
-----------

-  id3v2 header have the following fields alog the 10 first bytes in the
   file - byte 5 holds flags. 6th bit indicates extended tag - bytes
   6-10 are the tag size (not counting header)

-  id3v2 extended has a 10 bytes header after the regular id3v2 - bytes
   1-4 are the tag size (not counting header nor padding) - bytes 5-6
   holds some flags. Leftmost bit indicates CRC presence - bytes 6-10
   are the tag padding size (extra blank size within tag)

total size: 10 + tagsize + (10 + etagsize + padding if extended)

Based on id3v1 wikipedia docs: http://en.wikipedia.org/wiki/ID3 Based on
id3v2 docs: http://www.id3.org/id3v2.3.0
