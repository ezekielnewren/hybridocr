import unittest

from tests import dir_test_file_base, list_test_files


class TestTest(unittest.TestCase):

    def test_that_test_files_exist(self):
        for file in list_test_files():
            self.assertTrue((dir_test_file_base/file).exists())
