mp3hash
=======

`|Build Status| <https://travis-ci.org/jvrsantacruz/mp3hash>`_

Hashes music files ignoring meta-data.

Useful to detect the same song in different tagged files.

The following meta-data standards are supported:

::

    id3v1, id3v1 extended, id3v2.2, id3v2.3 and id3v.24

Known to work with: ``python2.6`` and ``python2.7``

Javier Santacruz (2012-2013)

Command line tool
=================

Similarly to other well-known tools like ``sha1sum`` or ``md5sum``, it
takes one or more files and outputs the hashes. It matches those
program's interface as much as possible.

::

    $ mp3hash *.mp3
    6611bc5b01a2fc6a6386a871e8c51f86e1f12b33 13_Hotel-California-(Gipsy-Kings).mp3
    6611bc5b01a2fc6a6386a871e8c51f86e1f12b33 14_Hotel-California-(Gipsy-Kings).mp3

You can see how it returns the same hash number for either file, even
though their tags are different, and so the data inside them.

::

    $ sha1sum *.mp3
    6a1d5f8317add10e205ae30174630b47645fb5b4  13_Hotel-California-(Gipsy-Kings).mp3
    c28d6976114d31df3366d9935eb0bedd36cf1f0b  14_Hotel-California-(Gipsy-Kings).mp3

The hash it's made strictly using the music data in the file. This is
done by calculating the tags sizes and ignoring them when calculating
the hash, thus hashing only the music data in the file.

The default hashing algorithm is ``sha-1``, but any algorithm can be
used as long it's supported by the Python's ``hashlib`` module. A
complete list of all available hashing algorithms can be obtained by
calling the program with the ``--list-algorithms`` flag.

::

    $ ./mp3hash --list-algorithms
    md5
    sha1
    sha224
    sha256
    sha384
    sha512

Any of the algorithms listed will be available to consume and hash the
content files.

::

    ./mp3hash --algorithm md5
    ac0fdd89454528d3fbdb19942a2e6653 13_Hotel-California-(Gipsy-Kings).mp3
    ac0fdd89454528d3fbdb19942a2e6653 14_Hotel-California-(Gipsy-Kings).mp3

You can even extend the library with your own hash functions, see the
*development* section to read about the API and how to use it.

Installation
============

It doesn't have any dependences besides ``python2.7+``.

In order to access to the ``mp3hash`` script, the package should be
installed.

::

    python setup.py install

Just afterwards, the ``mp3hash`` command should be available in path.

API
===

The main components are the ``mp3hash`` function and the ``TaggedFile``
class.

mp3hash
-------

``mp3hash.mp3hash`` will compute the hash on the music (and only the
music) of the file in the given path.

::

    >> from mp3hash import mp3hash
    >> mp3hash('/path/to/song.mp3')
    Out: 6611bc5b01a2fc6a6386a871e8c51f86e1f12b33

TaggedFile
----------

``mp3hash.TaggedFile`` class takes a file-like object supporting seek
with negative values and will parse all the sizes and offsets for the
meta-data tags stored within it.

::

    >> from mp3hash import TaggedFile
    >> with open('/path/to/song.mp3') as file:
        TaggedFile(file).has_id3v1
    Out: True

        TaggedFile(file).has_id3v2
    Out: True

        TaggedFile(file).filesize
    Out: 5315937

        TaggedFile(file).music_size
    Out: 5311714

        TaggedFile(file).startbyte
    Out: 4096

        TaggedFile(file).music_limits
    Out: (4096, 5315810)

Bring your own hash/checksum!
-----------------------------

Any object matching the ``update`` and ``hexdigest`` methods, follows
the hasher protocol and thereby can be used along with the ``mp3hash``
function.

If your method happens to not to match this protocol, you can always
adapt it. We could carry out a little experiment. It should be easy
enough for us to wrap the much faster ``adler32`` checksum algorithm to
make it work with ``mp3hash``.

The algorithm is available in the python standard module ``zlib``, as
``zlib.adler32``.

From the documentation:

    zlib.adler32(data[, value])

    Computes a Adler-32 checksum of data. [..] If value is present, it
    is used as the starting value of the checksum; otherwise, a fixed
    default value is used. This allows computing a running checksum over
    the concatenation of several inputs. [..]

::

    >> import zlib
    >> import mp3hash

    >> class Adler32Hasher(object):
          def __init__(self):
              self.value = None

          def update(self, data):
              if self.value is None:  # first call
                  self.value = zlib.adler32(data)
              else:
                  self.value = zlib.adler32(data, self.value)

          def hexdigest(self):
              return hex(self.value)

    >> mp3hash.mp3hash('/path/to/song.mp3', hasher=Adler32Hasher())
    Out: '0x40b1519d'

Developers, developers, developers!
===================================

Testing environment
-------------------

You're encouraged to use a *virtualenv*

::

    $ virtualenv --python python2 --distribute env
    $ source env/bin/activate

Once into the *virtualenv*, install the package and the testing
dependences.

::

    $(env) python setup.py develop
    $(env) pip install -r dev-reqs.txt

In order to perform the testing, use the ``nosetests`` test runner and
collector from the root of the project (same directory as of the
``setup.py`` file).

::

    $ nosetests

About id3v1
-----------

-  id3v1 is 128 bytes at the end of the file starting with 'TAG'
-  id3v1 extended is 227 bytes before regular id3v1 tag starting with
   'TAG+'

total size: 128 + (227 if extended)

Based on id3v1 wikipedia docs:

-  http://en.wikipedia.org/wiki/ID3

About id3v2
-----------

-  id3v2 has a 10 bytes header at the begining of the file.

   -  byte 5 holds flags. 4th bit indicates presence of footer in v2.4
   -  bytes 6-10 are the tag size (not counting header)

total size: header + tagsize + footer (if any)

Based on id3v2 docs:

-  http://id3.org/id3v2-00
-  http://id3.org/id3v2.3.0
-  http://id3.org/id3v2.4.0-structure

.. |Build
Status| image:: https://travis-ci.org/jvrsantacruz/mp3hash.png?branch=master
