import math

import gifmaker

from collections import namedtuple, deque
from PIL import Image, ImageFont, ImageDraw, ImageOps

Dimensions = namedtuple('Dimensions', ['width', 'height'])

def is_binary(this):
    """Determine whether or not 'this', is part of a binary file.

    The method for deciding whether or not the input is part of a binary file is
    taken from version 5.21 of the Unix File(1) command -- see src/encoding.c at
    https://github.com/file/file for more details if you're so inclined.
    """
    text_chars = (
        bytearray([7, 8, 9, 10, 12, 13, 27]) +
        bytearray(range(0x20, 0x7E)) +
        bytearray(range(0x80, 0xFF))
    )
    return bool(this.translate(None, text_chars))

def is_text(this):
    return not is_binary(this)

class FileHistory:
    def __init__(self, path, skip_empty=True):
        self.path = path
        self._commit_history = {}
        self._contents_to_commit = {}
        self._dimensions = Dimensions(width=0, height=0)
        self.skip_empty = skip_empty

    def add_commit_data(self, commit, blob):
        data_hash = blob.binsha
        if data_hash in self._contents_to_commit:
            self._commit_history[commit] = self._commit_history[
                self._contents_to_commit[data_hash]
            ]
            return
        lines = blob.data_stream.read().splitlines()
        if  self.skip_empty and not lines:
            return
        self._update_dimensions(lines)
        self._commit_history[commit] = lines
        self._contents_to_commit[data_hash] = commit

    def _update_dimensions(self, lines):
        widest_line = max([len(l) for l in lines] or [0])
        self._dimensions = Dimensions(
            width=max(widest_line, self._dimensions.width),
            height=max(len(lines), self._dimensions.height)
        )

    def in_commit(self, commit):
        return commit in self._commit_history

    def commit_contents(self, commit):
        return self._commit_history[commit]

    @property
    def width(self):
        return self._dimensions.width

    @property
    def height(self):
        return self._dimensions.height


class FileHistoryImages(FileHistory):
    def __init__(
            self, path, skip_empty,
            font=ImageFont.load_default(), border_size=1
    ):
        super().__init__(path, skip_empty)
        self.font = font
        self.border_size = border_size
        self.padding = border_size * 2
        self._path_dimensions = Dimensions(*font.getsize(path))
        self._x_scale = self._y_scale = 1

    def _draw_image(self, data):
        width = max(self._path_dimensions.width, super().width)
        height = super().height + self._path_dimensions.height
        image = ImageOps.expand(
            Image.new('1', (width, height), color=1),
            self.border_size
        )
        draw = ImageDraw.Draw(image)
        x_pos = y_start = self.border_size
        draw.text((x_pos, y_start), self.path, font=self.font)
        y_start += self._path_dimensions.height
        for y, line in enumerate(data):
            y_pos = y + y_start
            draw.line([(x_pos, y_pos), (len(line) + x_pos, y_pos)], fill=0)
        return image

    @property
    def width(self):
        return int(
            max(
                super().width + self.padding,
                self._path_dimensions.width + self.padding
            ) * self._x_scale
        )

    @property
    def height(self):
        return int(
            (super().height + self._path_dimensions.height + self.padding)
            * self._y_scale
        )

    def commit_image(self, commit):
        contents = self._commit_history[commit]
        return self._draw_image(contents)

    def scale(self, x_scale, y_scale):
        self._x_scale = x_scale
        self._y_scale = y_scale

def repo_gif(repo, outfile, max_width=1920, max_height=1200, skip_empty=True):
    commits = deque([repo.head.commit])
    while commits[0].parents:
        commits.appendleft(commits[0].parents[0])

    file_images = {}
    for commit in commits:
        for f in commit.tree.traverse(
                lambda i, d: i.type == 'blob' and
                is_text(i.data_stream.read(1024))
        ):
            file_images.setdefault(
                f.path, FileHistoryImages(f.path, skip_empty)
            ).add_commit_data(
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

    if width > max_width or height > max_height:
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
                image.paste(f.commit_image(commit.hexsha), (x, y))
            x += widest
            if x >= width:
                x = 0
                y += tallest
        yield image


if __name__ == '__main__':
    import sys, git
    r = git.Repo(sys.argv[1])
    repo_gif(r, sys.argv[2])
