import os, tempfile, shutil

import git

from unittest import TestCase
from PIL import Image

import code_image

class CodeImageTest(TestCase):
    def test_one_line_image(self):
        text = "hello world"
        image = code_image.image_for_text(text)
        self.assertEqual(image.size, (6*len(text), 11))

    def test_multi_line_image(self):
        text = "hello world\nhow are you"
        image = code_image.image_for_text(text)
        self.assertEqual(image.size, (66, 22))

    def test_image_from_repo(self):
        repo_dir = tempfile.mkdtemp()
        repo = git.Repo.init(repo_dir)
        with open(os.path.join(repo_dir, 'a-file.txt'), 'w') as f:
            f.write("hello world")
        repo.index.add(['a-file.txt'])
        repo.index.commit("initial commit")
        with open(os.path.join(repo_dir, 'a-file.txt'), 'a') as f:
            f.write("and goodbye again")
        repo.index.add(['a-file.txt'])
        repo.index.commit("add a line!")

        gif = code_image.images_for_repo(repo)
        self.assertEqual(2, len(gif))
        shutil.rmtree(repo_dir)
