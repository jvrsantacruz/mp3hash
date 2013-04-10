# mp3hash

Hashes music files ignoring meta-data.

Useful to detect the same song in different tagged files.

The following metadata standards are supported:

    id3v1, id3v1 extended, id3v2.2, id3v2.3 and id3v.24

Javier Santacruz (2012-2013)

# Command line usage

Similarly to `sha1sum` or `md5sum`, it takes one or more files and returns the hashes, in this way:

	$ ./mp3hash  *.mp3
	6611bc5b01a2fc6a6386a871e8c51f86e1f12b33 13_Hotel-California-(Gipsy-Kings).mp3
	6611bc5b01a2fc6a6386a871e8c51f86e1f12b33 14_Hotel-California-(Gipsy-Kings).mp3

It returns the same hash number, even though the tags are different, and so their regular hashes:

	$ sha1sum *.mp3
	6a1d5f8317add10e205ae30174630b47645fb5b4  13_Hotel-California-(Gipsy-Kings).mp3
	c28d6976114d31df3366d9935eb0bedd36cf1f0b  14_Hotel-California-(Gipsy-Kings).mp3

The hash it's made strictly using the music data in the file, by calculating the tags sizes and
omitting them.

The default hashing algorithm is `sha-1`, but any algorithm can be used as long it's supported by
the Python's `hashlib` module. A complete list of all available hashing algorithms can be obtained
by calling the program with the `--list-algorithms`.

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


# Installation

It doesn't have any dependences besides `python2.7+`.
In order to access to the `mp3hash` script, the package should be installed.

    python setup.py install

And the `mp3hash` command should be available in path.

# API

The main components are the mp3hash function and the TaggedFile class.

- mp3hash will compute the hash on the music (and only the music)
  of the file in the given path.

    >> from mp3hash import mp3hash
    >> mp3hash('/path/to/song.mp3')
    Out: 6611bc5b01a2fc6a6386a871e8c51f86e1f12b33

- TaggedFile class takes a file-like object supporting
  seek and negative values for seek and will parse all the sizes
  for the metadata stored within it.

    >> from mp3hash import TaggedFile
    >> with open('/path/to/song.mp3') as file:
           TaggedFile(file).has_id3v2
    Out: True


# Developers, developers, developers!

## Testing environment

You're adviced to use a virtualenv

    $ virtualenv --python python2 --distribute env
    $ . env/bin/activate

Once into the virtualenv, install the package and the testing dependences.

    $(env) python setup.py develop
    $(env) pip install -r dev-reqs.txt

In order to perform the testing, run 'nosetests' from the root of the project (same dir of setup.py).

    $ nosetests

## About id3v1

- id3v1 is 128 bytes at the end of the file starting with 'TAG'
- id3v1 extended is 227 bytes before regular id3v1 tag starting with 'TAG+'

total size: 128 + (227 if extended)

id3v1 is 128 bytes at the end of the file starting with 'TAG'
id3v1 extended is 227 bytes before regular id3v1 tag starting with 'TAG+'

total size: 128 + (227 if extended)

## About id3v2

id3v2 has a 10 bytes header at the begining of the file.
      byte 5 holds flags. 4th bit indicates presence of footer in v2.4
      bytes 6-10 are the tag size (not counting header)

total size: header + tagsize + footer (if any)

Based on id3v1 wikipedia docs: http://en.wikipedia.org/wiki/ID3
Based on id3v2 docs:

- http://id3.org/id3v2-00
- http://www.id3.org/id3v2.3.0
- http://id3.org/id3v2.4.0-structure
