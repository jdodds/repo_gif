import tempfile, os, math, resource

import gifmaker

from collections import namedtuple, deque
from PIL import Image, ImageFont, ImageDraw

Dimensions = namedtuple('Dimensions', ['width', 'height'])

def is_binary_string(s):
    """Determine whether or not some string, s, is part of a binary file.

    The method for deciding whether or not the input is part of a binary file is
    taken from version 5.21 of the Unix File(1) command -- see src/encoding.c at
    https://github.com/file/file for more details if you're so inclined.
    """
    text_chars = (
        bytearray([7, 8, 9, 10, 12, 13, 27]) +
        bytearray(range(0x20, 0x7E)) +
        bytearray(range(0x80, 0xFF))
    )
    return bool(s.translate(None, text_chars))

class ImagesForFile:
    def __init__(self, path):
        self._path = path
        self._commit_images = {}
        self._seen_hashes = {}
        self._dimensions = Dimensions(width=0, height=0)

    def add_commit_data(self, commit, blob):
        if blob.binsha in self._seen_hashes:
            self._commit_images[commit] = self._commit_images[
                self._seen_hashes[blob.binsha]
            ]
            return
        data = blob.data_stream.read().splitlines()
        if data:
            widest_line = max(len(l) for l in data)
            self._dimensions = Dimensions(
                width=max(widest_line, self._dimensions.width),
                height=max(len(data), self._dimensions.height)
            )
        image = Image.new('1', self._dimensions, color=1)
        draw = ImageDraw.Draw(image)
        for y, line in enumerate(data):
            draw.line([(0,y), (len(line), y)], fill=0)
        self._commit_images[commit] = image
        self._seen_hashes[blob.binsha] = commit


    def in_commit(self, commit):
        return commit in self._commit_images

    def commit_image(self, commit):
        return self._commit_images[commit]

    @property
    def width(self):
        return self._dimensions.width

    @property
    def height(self):
        return self._dimensions.height

    def scale(self, x_factor, y_factor):
        sizes = [
            (int(i.size[0] * x_factor), int(i.size[1] * y_factor))
            for i in self._commit_images.values()
        ]
        width = max(s[0] for s in sizes)
        height = max(s[1] for s in sizes)
        self._dimensions = Dimensions(width=width, height=height)

def repo_gif(repo, outfile, max_width=1920, max_height=1200):
    commits = deque([repo.head.commit])
    while commits[0].parents:
        commits.appendleft(commits[0].parents[0])

    file_images = {}
    for commit in commits:
        for f in commit.tree.traverse(
                lambda i,d: i.type=='blob' and
                not is_binary_string(i.data_stream.read(1024))
        ):
            file_images.setdefault(f.path, ImagesForFile(f.path)).add_commit_data(
                commit.hexsha, f
            )

    images = file_images.values()
    widest = max(f.width for f in images)
    tallest = max(f.height for f in images)
    num_images = len(images)
    images_per_row = math.ceil(math.sqrt(num_images))
    num_rows = math.ceil(num_images / images_per_row)
    height = tallest * num_rows
    width = widest * images_per_row

    width_ratio = max_width / width
    height_ratio = max_height / height
    for image in images:
        image.scale(width_ratio, height_ratio)

    widest = max(f.width for f in images)
    tallest = max(f.height for f in images)

    height = tallest * num_rows
    width = widest * images_per_row

    with open(outfile, 'wb') as fp:
        gifmaker.makedelta(
            fp,
            frames(commits, width, height, widest, tallest, images)
        )

def frames(commits, width, height, widest, tallest, images):
    for commit in commits:
        image = Image.new('1', (width, height), color=1)
        x = 0
        y = 0
        for f in images:
            if f.in_commit(commit.hexsha):
                image.paste(f.commit_image(commit.hexsha), (x,y))
            x += widest
            if x >= width:
                x = 0
                y += tallest
        yield image


if __name__ == '__main__':
    import sys, git
    r = git.Repo(sys.argv[1])
    repo_gif(r, sys.argv[2])
