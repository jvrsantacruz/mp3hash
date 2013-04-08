#-*- coding: utf-8 -*-

from hamcrest import is_, assert_that

from mp3hash import parse_7bitint


class Test7bitint(object):
    def test_parses_numbers_in_the_right_order(self):
        read_byte_string = [0x08, 0x04, 0x02, 0x01]

        parse = parse_7bitint(read_byte_string)

        # 0x01 << 0 + 0x02 << 7 + 0x04 << 14 + 0x08 << 21
        assert_that(parse, is_(16843009))

    def test_zeroes_8th_bit(self):
        # 0x80 is 1000 0000 with only the 8th bit on
        read_byte_string = [0x80, 0x80, 0x80, 0x80]

        parse = parse_7bitint(read_byte_string)

        assert_that(parse, is_(0))

    def test_parses_8th_bit_while_keeping_the_rest(self):
        # 0xFF (11111 1111) will become 0x7F (0111 1111)
        read_byte_string = [0xFF, 0xFF, 0xFF, 0xFF]

        parse = parse_7bitint(read_byte_string)

        # 0x7F << 0 + 0x7F << 7 + 0x7F << 14 + 0x7F << 21
        assert_that(parse, is_(268435455))
