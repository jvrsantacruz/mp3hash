#-*- coding: utf-8 -*-

import sys
import errno

try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO  # python3


from doublex import Spy, called
from hamcrest import assert_that, contains_string


from cli import main


class TestCLI(object):
    def setup(self):
        # monkeypatchs sys
        # I know, I know...
        self.old_stdout = sys.stdout
        self.old_stderr = sys.stderr

        self.stdout = sys.stdout = StringIO()
        self.stderr = sys.stderr = StringIO()

        self.exit = Spy().exit
        self.old_sys_exit = sys.exit
        sys.exit = self.exit

        self.argv = [sys.argv[0]]
        self.old_sys_argv = sys.argv
        sys.argv = self.argv

    def teardown(self):
        sys.stdout = self.old_stdout
        sys.stderr = self.old_stderr
        sys.exit = self.old_sys_exit
        sys.argv = self.old_sys_argv

    def test_main_with_no_arguments_stdouts_error(self):
        main()

        assert_that(self.stdout.getvalue(),
                    contains_string(u'Insufficient arguments'))

    def test_main_with_no_arguments_exits_with_invalid_argument(self):
        main()

        assert_that(self.exit, called().with_args(errno.EINVAL))

    def test_main_with_negative_maxbytes_value_stdouts_error(self):
        self.argv.extend(['--maxbytes', '-5'])

        main()

        assert_that(self.stdout.getvalue(),
                    contains_string(u'Invalid value for --maxbytes'))

    def test_main_with_negative_maxbytes_exits_with_invalid_argument(self):
        self.argv.extend(['--maxbytes', '-5'])

        main()

        assert_that(self.exit, called().with_args(errno.EINVAL))

    def test_main_with_0_maxbytes_value_stdouts_error(self):
        self.argv.extend(['--maxbytes', '0'])

        main()

        assert_that(self.stdout.getvalue(),
                    contains_string(u'Invalid value for --maxbytes'))

    def test_main_with_0_maxbytes_exits_with_invalid_argument(self):
        self.argv.extend(['--maxbytes', '0'])

        main()

        assert_that(self.exit, called().with_args(errno.EINVAL))
