from cStringIO import StringIO

from hamcrest import assert_that, is_

from mp3hash import TaggedFile, ID3V2_HEADER_SIZE, ID3V2_EXTENDED_HEADER_SIZE


VERSION = 0x03
REVISION = 0x0
FLAGS = 0x40  # extension flag up
RAW_SIZE = [0x0, 0x0, 0x02, 0x01]  # (2 << 7) + 1 = 257
SIZE = 257

V1_RAW_HEADER = [VERSION, REVISION, FLAGS] + RAW_SIZE
V1_HEADER = 'ID3' + ''.join(chr(n) for n in V1_RAW_HEADER)

TAGGED = V1_HEADER + '\n' * SIZE


class TestID3v2Extended(object):
    def test_detects_id3v2_extended_tags(self):
        file = StringIO(TAGGED)

        tagged = TaggedFile(file)

        assert_that(tagged.has_id3v2ext)
