import subprocess, tempfile, os, math

from collections import namedtuple
from PIL import Image, ImageFont, ImageDraw

Dimensions = namedtuple('Dimensions', ['width', 'height'])

class ImagesForFile:
    def __init__(self, path, font=ImageFont.load_default()):
        self._path = path
        self._data = {}
        self._font = font
        self._dimensions = Dimensions(width=0, height=0)
        self._line_height = 0

    def add_commit_data(self, commit, data):
        self._data[commit] = data
        if data:
            line_sizes = [self._font.getsize(l) for l in data]
            tallest_line = max([l[1] for l in line_sizes])
            widest_line = max([l[0] for l in line_sizes])
            data_height = len(data)*tallest_line
            self._dimensions = Dimensions(
                width=max(widest_line, self._dimensions.width),
                height=max(data_height, self._dimensions.height)
            )
            self._line_height = max(tallest_line, self._line_height)

    def in_commit(self, commit):
        return commit in self._data

    def commit_image(self, commit):
        lines = self._data[commit]
        image = Image.new('1', self._dimensions, color=1)
        draw = ImageDraw.Draw(image)
        for i, line in enumerate(lines):
            y_position = i*self._line_height
            draw.text((0, y_position), line, font=self._font)
        return image

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

    file_images = {}
    for commit in reversed(commits):
        for f in commit.tree.traverse(lambda i,d: i.type=='blob'):
            file_images.setdefault(f.path, ImagesForFile(f.path)).add_commit_data(
                commit.hexsha,
                f.data_stream.read().splitlines()
            )

    widest = max(f.width for f in file_images.values())
    tallest = max(f.height for f in file_images.values())
    num_images = len(file_images)
    images_per_row = math.ceil(math.sqrt(num_images))
    num_rows = math.ceil(num_images / images_per_row)
    height = tallest * num_rows
    width = widest * images_per_row
    gif_frames = []
    for commit in reversed(commits):
        image = Image.new('1', (width, height), color=1)
        x = 0
        y = 0
        for f in file_images.values():
            if f.in_commit(commit.hexsha):
                image.paste(f.commit_image(commit.hexsha), (x,y))
            x += widest
            if x == width:
                x = 0
                y += tallest
        gif_frames.append(image)

    tempfiles = []
    for frame in gif_frames:
        path = tempfile.mkstemp('.png')[1]
        frame.save(path)
        tempfiles.append(path)
    command = [
        'convert',
        '-delay', '20',
    ]
    command += tempfiles
    command += ['-loop', '0']
    command.append(outfile)
    subprocess.call(command)
    for tf in tempfiles:
        os.remove(tf)


if __name__ == '__main__':
    import sys, git
    r = git.Repo(sys.argv[1])
    repo_gif(r, sys.argv[2])
