from PIL import Image, ImageFont, ImageDraw

def image_for_text(text):
    font = ImageFont.load_default()
    lines = text.splitlines()
    return draw_lines_with_font(lines, font)

def draw_lines_with_font(lines, font):
    line_sizes = [font.getsize(l) for l in lines]
    line_height = max([l[1] for l in line_sizes])

    image = image_fitting(line_sizes)
    draw = ImageDraw.Draw(image)
    y = 0
    for line in lines:
        draw.text((0, y), line, font=font)
        y += line_height
    return image

def image_fitting(line_sizes):
    dimensions = (
        max([l[0] for l in line_sizes]),
        sum([l[1] for l in line_sizes])
    )
    return Image.new('1', dimensions, color=1)

def images_for_repo(repo):
    head_commit = repo.head.commit
    commits = [head_commit]
    while len(commits[-1].parents) != 0:
        commits.append(commits[-1].parents[0])
    images = [image_for_text(t) for t in
              [c.tree.blobs[0].data_stream.read() for c in reversed(commits)]]
    return images
