#-*- coding: utf-8 -*-

from cStringIO import StringIO

from hamcrest import assert_that, is_

from mp3hash import TaggedFile, ID3V2_HEADER_SIZE, ID3V2_FOOTER_SIZE


NOT_TAGGED = '\n' * ID3V2_HEADER_SIZE
TAGGED = 'ID3' + '\n' * (ID3V2_HEADER_SIZE - 3)
TAGGED_AND_FILLED = TAGGED + '\n' * 512


class TestID3v2(object):
    def test_detects_id3v2_tags(self):
        file = StringIO(TAGGED)

        tagged = TaggedFile(file)

        assert_that(tagged.has_id3v2)

    def test_detects_id3v2_tags_even_with_content(self):
        file = StringIO(TAGGED_AND_FILLED)

        tagged = TaggedFile(file)

        assert_that(tagged.has_id3v2)

    def test_detects_when_there_is_no_id3v1_tag(self):
        file = StringIO(NOT_TAGGED)

        tagged = TaggedFile(file)

        assert_that(not tagged.has_id3v2)

    def test_says_there_is_no_tag_when_file_is_too_small(self):
        file = StringIO()

        tagged = TaggedFile(file)

        assert_that(not tagged.has_id3v2)


VERSION = 0x03
REVISION = 0x0
FLAGS = 0x0
RAW_SIZE = [0x0, 0x0, 0x02, 0x01]  # (2 << 7) + 1 = 257
SIZE = 257

PARSED_HEADER = ('ID3', VERSION, REVISION, FLAGS, SIZE)
RAW_HEADER = [VERSION, REVISION, FLAGS] + RAW_SIZE
HEADER = 'ID3' + ''.join(map(chr, RAW_HEADER))


class TestID3v2Sizes(object):
    def test_header_is_read_properly(self):
        file = StringIO(HEADER)

        tagged = TaggedFile(file)

        assert_that(tagged._id3v2_header, is_(PARSED_HEADER))

    def test_size_is_read_from_header_correctly(self):
        file = StringIO(HEADER)

        tagged = TaggedFile(file)

        assert_that(tagged.id3v2_size, is_(SIZE + ID3V2_HEADER_SIZE))

    def test_id3v2_totalsize_is_id3v2_size(self):
        assert_that(TaggedFile.id3v2_totalsize, is_(TaggedFile.id3v2_size))


VERSION_v24 = 0x4
FLAGS_v24 = 0x10  # footer present set

PARSED_HEADER_v24 = ('ID3', VERSION_v24, REVISION, FLAGS_v24, SIZE)
RAW_HEADER_v24 = [VERSION_v24, REVISION, FLAGS_v24] + RAW_SIZE
HEADER_v24 = 'ID3' + ''.join(map(chr, RAW_HEADER_v24))


class TestID3v24Sizes(object):
    def test_header_is_read_properly(self):
        file = StringIO(HEADER_v24)

        tagged = TaggedFile(file)

        assert_that(tagged._id3v2_header, is_(PARSED_HEADER_v24))

    def test_size_adds_footer_size(self):
        file = StringIO(HEADER_v24)

        tagged = TaggedFile(file)

        assert_that(tagged.id3v2_size, is_(SIZE + ID3V2_HEADER_SIZE + ID3V2_FOOTER_SIZE))
