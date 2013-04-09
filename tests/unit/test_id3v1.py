#-*- coding: utf-8 -*-

from cStringIO import StringIO

from hamcrest import assert_that, is_

from mp3hash import TaggedFile, ID3V1_SIZE


MP3_ID3v1_NOT_TAGGED = '\n' * ID3V1_SIZE
MP3_ID3v1_TAGGED = 'TAG' + '\n' * (ID3V1_SIZE - 3)
MP3_ID3v1_TAGGED_AND_FILLED = '\n' * 512 + MP3_ID3v1_TAGGED


class TestID3v1(object):
    def test_detects_id3v1_tags(self):
        file = StringIO(MP3_ID3v1_TAGGED)

        tagged = TaggedFile(file)

        assert_that(tagged.has_id3v1)

    def test_detects_id3v1_tags_even_with_content(self):
        file = StringIO(MP3_ID3v1_TAGGED_AND_FILLED)

        tagged = TaggedFile(file)

        assert_that(tagged.has_id3v1)

    def test_detects_when_there_is_no_id3v1_tag(self):
        file = StringIO(MP3_ID3v1_NOT_TAGGED)

        tagged = TaggedFile(file)

        assert_that(not tagged.has_id3v1)

    def test_says_there_is_no_tag_when_file_is_too_small(self):
        file = StringIO()

        tagged = TaggedFile(file)

        assert_that(not tagged.has_id3v1)


class TestID3v1Size(object):
    def test_id3v1_size_is_128_if_there_is_tag(self):
        file = StringIO(MP3_ID3v1_TAGGED)

        tagged = TaggedFile(file)

        assert_that(tagged.id3v1_size, is_(ID3V1_SIZE))

    def test_id3v1_size_is_0_if_no_tag_is_present(self):
        file = StringIO(MP3_ID3v1_NOT_TAGGED)

        tagged = TaggedFile(file)

        assert_that(tagged.id3v1_size, is_(0))
