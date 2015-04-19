from PIL import Image, ImageFont, ImageDraw

def from_text(text):
    font = ImageFont.load_default()
    lines = text.splitlines()
    return draw_lines_with_font(lines, font)

def draw_lines_with_font(lines, font):
    line_sizes = [font.getsize(l) for l in lines]
    line_height = max([l[1] for l in line_sizes])

    image = create_image_fitting(line_sizes)
    draw = ImageDraw.Draw(image)
    y = 0
    for line in lines:
        draw.text((0, y), line, font=font)
        y += line_height
    return image

def create_image_fitting(line_sizes):
    dimensions = (
        max([l[0] for l in line_sizes]),
        sum([l[1] for l in line_sizes])
    )
    return Image.new('1', dimensions, color=1)

def from_repo(repo):
    head_commit = repo.head.commit
    commits = [head_commit]
    while len(commits[-1].parents) != 0:
        commits.append(commits[-1].parents[0])
    images = [from_text(t) for t in
              [c.tree.blobs[0].data_stream.read() for c in reversed(commits)]]
    return images
