from PIL import Image, ImageFont, ImageDraw

class TextImage:
    def __init__(self, text):
        self.font = ImageFont.load_default()
        self.lines = text.splitlines()
        line_sizes = [self.font.getsize(l) for l in self.lines]
        self._dimensions = (
            max([l[0] for l in line_sizes]),
            sum([l[1] for l in line_sizes])
        )
        self.line_height = max([l[1] for l in line_sizes])

    @property
    def dimensions(self):
        return self._dimensions

    def save(self, path):
        image = Image.new('1', self.dimensions, color=1)
        draw = ImageDraw.Draw(image)
        y = 0
        for line in self.lines:
            draw.text((0, y), line, font=self.font)
            y += self.line_height
        image.save(path)
