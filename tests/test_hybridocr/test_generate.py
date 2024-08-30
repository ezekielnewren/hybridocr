import unittest

import hybridocr.generate as generate
from hybridocr.core import *

class TestGenerate(unittest.TestCase):

    def test_text_to_image(self):
        # Arrange: Setup your test case
        input_value = "input"
        expected_output = "expected_output"

        result = generate.text_to_image("Hello\nworld.")

        # Assert: Check if the output matches the expected output
        self.assertIsNotNone(result)

        show_image(result)

        pass
