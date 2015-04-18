import os, tempfile

from unittest import TestCase
from PIL import Image

from code_image import TextImage

class CodeImageTest(TestCase):
    def test_one_line_image(self):
        text = "hello world"
        image = TextImage(text)
        path = tempfile.mkstemp('.png')[1]
        image.save(path)
        check = Image.open(path)
        self.assertEqual(check.size, (6*len(text), 11))
        os.remove(path)

    def test_multi_line_iamge(self):
        text = "hello world\nhow are you"
        image = TextImage(text)
        path = tempfile.mkstemp('.png')[1]
        image.save(path)
        check = Image.open(path)
        self.assertEqual(check.size, (66, 22))
        os.remove(path)
