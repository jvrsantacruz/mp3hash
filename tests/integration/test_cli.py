#-*- coding: utf-8 -*-

import errno
import subprocess

from hamcrest import assert_that, contains_string, is_


SCRIPT = 'mp3hash'


def call(*args):
    return subprocess.call([SCRIPT] + list(args))


def check_output(*args):
    try:
        return subprocess.check_output([SCRIPT] + list(args))
    except subprocess.CalledProcessError as output:
        return output.output


class TestCLI(object):
    def test_main_with_no_arguments_stdouts_error(self):
        output = check_output()

        assert_that(output, contains_string(u'Insufficient arguments'))

    def test_main_with_no_arguments_exits_with_invalid_argument(self):
        retcode = call()

        assert_that(retcode, is_(errno.EINVAL))

    def test_main_with_negative_maxbytes_value_stdouts_error(self):
        output = check_output('--maxbytes', '-5', '*')

        assert_that(output, contains_string(u'Invalid value for --maxbytes'))

    def test_main_with_negative_maxbytes_exits_with_invalid_argument(self):
        retcode = call('--maxbytes', '-5', '*')

        assert_that(retcode, is_(errno.EINVAL))

    def test_main_with_0_maxbytes_value_stdouts_error(self):
        output = check_output('--maxbytes', '0', '*')

        assert_that(output, contains_string(u'Invalid value for --maxbytes'))

    def test_main_with_0_maxbytes_exits_with_invalid_argument(self):
        retcode = call('--maxbytes', '0', '*')

        assert_that(retcode, is_(errno.EINVAL))
