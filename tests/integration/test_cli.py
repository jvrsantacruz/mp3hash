#-*- coding: utf-8 -*-

import os
import errno
import hashlib
import subprocess

from hamcrest import *
from tests.integration import SONG1_PATH, SONG2_PATH, SONG1_PATH2

import mp3hash


OK = 0
SCRIPT = 'mp3hash'
NON_EXISTENT_PATH = '/non/existent/path'
NON_EXISTENT_ALGORITHM = 'I am not a hash'
NON_EXISTENT_FILE = 'nonexistent.txt'


def call(*args):
    process = subprocess.Popen(
        args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    stdout, unused_stderr = process.communicate()
    retcode = process.wait()

    return retcode, stdout


class TestParameterValidation(object):
    def test_no_arguments_stdouts_error(self):
        retcode, output = call(SCRIPT)

        assert_that(output, contains_string(u'Insufficient arguments'))

    def test_no_arguments_exits_with_invalid_argument(self):
        retcode, output = call(SCRIPT)

        assert_that(retcode, is_(errno.EINVAL))

    def test_non_existent_path_returns_ok(self):
        retcode, output = call(SCRIPT, NON_EXISTENT_PATH)

        assert_that(retcode, is_(OK))

    def test_non_existent_path_outputs_error(self):
        retcode, output = call(SCRIPT, NON_EXISTENT_PATH)

        assert_that(output, contains_string('does not exist'))


class TestListAlgorithmsOption(object):
    def test_list_algorithms_returns_ok(self):
        retcode, output = call(SCRIPT, '--list-algorithms')

        assert_that(retcode, is_(OK))


class TestMaxbytesOption(object):
    def test_maxbytes_option_changes_maxbytes_used(self):
        maxbytes = 1000
        hash = mp3hash.mp3hash(SONG1_PATH, maxbytes=maxbytes)

        retcode, output = call(SCRIPT, SONG1_PATH, '--maxbytes', str(maxbytes))

        assert_that(output, starts_with(hash))

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


class TestHashOption(object):
    def test_existent_file_outputs_hash_only_if_hash_opt_is_present(self):
        hash = mp3hash.mp3hash(SONG1_PATH)

        retcode, output = call(SCRIPT, SONG1_PATH, '--hash')

        assert_that(output, is_(hash + '\n'))


class TestAlgorithmOption(object):
    def test_non_existent_algorithm_outputs_one_line_error(self):
        retcode, output = call(
            SCRIPT, '--algorithm', NON_EXISTENT_ALGORITHM, '*')

        assert_that(output.count('\n'), is_(1))

    def test_non_existent_algorithm_outputs_error(self):
        retcode, output = call(
            SCRIPT, '--algorithm', NON_EXISTENT_ALGORITHM, '*')

        assert_that(output, all_of(
            contains_string('Unknown'),
            contains_string('algorithm')
        ))

    def test_default_algorithm_is_sha1(self):
        hasher = hashlib.new('sha1')
        hash = mp3hash.mp3hash(SONG1_PATH, hasher=hasher)

        retcode, output = call(SCRIPT, SONG1_PATH)

        assert_that(output, starts_with(hash))

    def test_algorithm_option_changes_algorithm_used(self):
        algorithm = 'md5'
        hasher = hashlib.new(algorithm)
        hash = mp3hash.mp3hash(SONG1_PATH, hasher=hasher)

        retcode, output = call(SCRIPT, SONG1_PATH, '--algorithm', algorithm)

        assert_that(output, starts_with(hash))


class TestOutputOption(object):
    def setup(self):
        try:
            os.unlink(NON_EXISTENT_FILE)
        except OSError:
            pass

    def test_output_changes_output_and_stdouts_nothing(self):
        retcode, output = call(SCRIPT, SONG1_PATH,
                               '--output', NON_EXISTENT_FILE)

        assert_that(output, is_(u''))

    def test_output_redirects_output_to_file_in_given_path(self):
        hash = mp3hash.mp3hash(SONG1_PATH)
        filename = os.path.basename(SONG1_PATH)

        retcode, output = call(SCRIPT, SONG1_PATH,
                               '--output', NON_EXISTENT_FILE)

        with open(NON_EXISTENT_FILE) as output_file:
            assert_that(output_file.read(), is_(hash + u' ' + filename + '\n'))


class TestHashing(object):
    def test_existent_file_returns_ok(self):
        retcode, output = call(SCRIPT, SONG1_PATH2)

        assert_that(retcode, is_(OK))

    def test_existent_file_outputs_one_single_line(self):
        retcode, output = call(SCRIPT, SONG1_PATH)

        assert_that(output.count('\n'), is_(1))

    def test_existent_file_outputs_hash_space_filename(self):
        hash = mp3hash.mp3hash(SONG1_PATH)
        filename = os.path.basename(SONG1_PATH)

        retcode, output = call(SCRIPT, SONG1_PATH)

        assert_that(output, is_(hash + u' ' + filename + '\n'))

    def test_several_existent_files_returns_ok(self):
        paths = [SONG1_PATH, SONG2_PATH]

        retcode, output = call(SCRIPT, *paths)

        assert_that(retcode, is_(OK))

    def test_several_existent_files_outputs_several_lines(self):
        paths = [SONG1_PATH, SONG2_PATH]

        retcode, output = call(SCRIPT, *paths)

        assert_that(output.count('\n'), is_(len(paths)))
