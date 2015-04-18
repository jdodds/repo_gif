import os, tempfile

from unittest import TestCase
from PIL import Image

import code_image

class CodeImageTest(TestCase):
    def test_one_line_image(self):
        text = "hello world"
        image = code_image.from_text(text)
        self.assertEqual(image.size, (6*len(text), 11))

    def test_multi_line_image(self):
        text = "hello world\nhow are you"
        image = code_image.from_text(text)
        self.assertEqual(image.size, (66, 22))
