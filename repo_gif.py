import tempfile, os, math, resource

import gifmaker

from collections import namedtuple
from PIL import Image, ImageFont, ImageDraw

Dimensions = namedtuple('Dimensions', ['width', 'height'])

def is_binary_string(s):
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

def repo_gif(repo, outfile):
    commits = [repo.head.commit]
    while len(commits[-1].parents) != 0:
        commits.append(commits[-1].parents[0])
    commits.reverse()

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
    gif_frames = []

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
            if x == width:
                x = 0
                y += tallest
        yield image

if __name__ == '__main__':
    import sys, git
    r = git.Repo(sys.argv[1])
    repo_gif(r, sys.argv[2])
