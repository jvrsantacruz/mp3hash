#-*- coding: utf-8 -*-

import os
import shutil
import hashlib

import mutagen

from hamcrest import *
from nose.tools import *

from mp3hash import mp3hash


class BaseTest(object):

    def setup(self):
        self.song1_path = 'tests/file1.mp3'
        self.song2_path = 'tests/file2.mp3'

        shutil.copy(self.song1_path, self.song2_path)

        self.song1_size = os.path.getsize(self.song1_path)
        self.song2_size = os.path.getsize(self.song2_path)

    def test_setup(self):
        assert_that(self.song1_size, is_(equal_to(self.song2_size)))

    def tearDown(self):
        try:
            #os.unlink(self.song2_path)
            pass
        except OSError:
            pass


class TestIdenticFiles(BaseTest):
    def test_mp3hash(self):
        hash1 = mp3hash(self.song1_path)
        hash2 = mp3hash(self.song2_path)
        assert_that(hash1, is_(equal_to(hash2)))

    def test_algs(self):
        "Test generator for every algorithm"
        for alg in hashlib.algorithms:
            self.check_algs(alg)

    def check_algs(self, alg):
        hash1 = mp3hash(self.song1_path, alg=alg)
        hash2 = mp3hash(self.song2_path, alg=alg)
        assert_that(hash1, is_(equal_to(hash2)))

    def test_maxbytes_all(self):
        "Test generator for multiple sizes"
        for num in range(1, self.song1_size, 250):
            self.check_num(num)

    def check_num(self, maxbytes):
        hash1 = mp3hash(self.song1_path, maxbytes=maxbytes)
        hash2 = mp3hash(self.song2_path, maxbytes=maxbytes)
        assert_that(hash1, is_(equal_to(hash2)))

    @raises(ValueError)
    def test_maxbytes_negative(self):
        mp3hash(self.song1_path, maxbytes=-15)

    @raises(ValueError)
    def test_maxbytes_0(self):
        mp3hash(self.song1_path, maxbytes=-15)


class TestSameDataButNoTags(TestIdenticFiles):
    def setup(self):
        super(TestSameDataButNoTags, self).setup()
        f = mutagen.File(self.song2_path)
        f.clear()
        f.save()
