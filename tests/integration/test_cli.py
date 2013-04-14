#-*- coding: utf-8 -*-

import errno
import subprocess

from hamcrest import assert_that, contains_string, is_, all_of

from tests.integration import SONG1_PATH, SONG2_PATH


OK = 0
SCRIPT = 'mp3hash'
NON_EXISTENT_PATH = '/non/existent/path'
NON_EXISTENT_ALGORITHM = 'I am not a hash'


def call(*args):
    try:
        return 0, subprocess.check_output(args, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as command:
        return command.returncode, command.output


class TestCLI(object):
    def test_no_arguments_stdouts_error(self):
        retcode, output = call(SCRIPT)

        assert_that(output, contains_string(u'Insufficient arguments'))

    def test_no_arguments_exits_with_invalid_argument(self):
        retcode, output = call(SCRIPT)

        assert_that(retcode, is_(errno.EINVAL))

    def test_negative_maxbytes_value_stdouts_error(self):
        retcode, output = call(SCRIPT, '--maxbytes', '-5', '*')

        assert_that(output, contains_string(u'Invalid value for --maxbytes'))

    def test_negative_maxbytes_exits_with_invalid_argument(self):
        retcode, output = call(SCRIPT, '--maxbytes', '-5', '*')

        assert_that(retcode, is_(errno.EINVAL))

    def test_maxbytes_value_stdouts_error(self):
        retcode, output = call(SCRIPT, '--maxbytes', '0', '*')

        assert_that(output, contains_string(u'Invalid value for --maxbytes'))

    def test_maxbytes_exits_with_invalid_argument(self):
        retcode, output = call(SCRIPT, '--maxbytes', '0', '*')

        assert_that(retcode, is_(errno.EINVAL))

    def test_list_algorithms_returns_ok(self):
        retcode, output = call(SCRIPT, '--list-algorithms')

        assert_that(retcode, is_(OK))

    def test_non_existent_path_returns_ok(self):
        retcode, output = call(SCRIPT, NON_EXISTENT_PATH)

        assert_that(retcode, is_(OK))

    def test_non_existent_path_outputs_error(self):
        retcode, output = call(SCRIPT, NON_EXISTENT_PATH)

        assert_that(output, contains_string('does not exist'))

    def test_non_existent_algorithm_outputs_error(self):
        retcode, output = call(
            SCRIPT, '--algorithm', NON_EXISTENT_ALGORITHM, '*')

        assert_that(output, all_of(
            contains_string('Unknown'),
            contains_string('algorithm')
        ))

    def test_non_existent_algorithm_outputs_one_line_error(self):
        retcode, output = call(
            SCRIPT, '--algorithm', NON_EXISTENT_ALGORITHM, '*')

        assert_that(output.count('\n'), is_(1))

    def test_existent_file_returns_ok(self):
        retcode, output = call(SCRIPT, SONG1_PATH)

        assert_that(retcode, is_(OK))

    def test_several_existent_files_returns_ok(self):
        retcode, output = call(SCRIPT, SONG1_PATH, SONG2_PATH)

        assert_that(retcode, is_(OK))
