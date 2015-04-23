import os, tempfile, shutil

import git

from unittest import TestCase
from PIL import Image

import repo_gif

class RepoGif(TestCase):
    def setUp(self):
        self.repo_dir = tempfile.mkdtemp()
        self.repo = git.Repo.init(self.repo_dir)

    def tearDown(self):
        shutil.rmtree(self.repo_dir)

    def test_image_from_repo(self):
        with open(os.path.join(self.repo_dir, 'a-file.txt'), 'w') as f:
            f.write("hello world\n")
        self.repo.index.add(['a-file.txt'])
        self.repo.index.commit("initial commit")
        with open(os.path.join(self.repo_dir, 'a-file.txt'), 'a') as f:
            f.write("and goodbye again\n")
        self.repo.index.add(['a-file.txt'])
        self.repo.index.commit("add a line!")

        gif_path = tempfile.mkstemp('.gif')[1]
        gif = repo_gif.repo_gif(self.repo, gif_path)
        print(gif_path)
