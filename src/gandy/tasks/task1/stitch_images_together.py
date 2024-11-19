from PIL import Image

def stack_horizontally(images):
    min_height = min(i.height for i in images)

    total_width = 0
    for idx in range(len(images)):
        img = images[idx]

        if img.height > min_height:
            images[idx] = img.resize((int(img.width / img.height * min_height), min_height), Image.ANTIALIAS)

        total_width += images[idx].width

    merged = Image.new('RGB', (total_width, min_height))
    offset = 0
    for img in images:
        merged.paste(img, (0, offset))
        offset += img.width

    return merged

def stack_vertically(images):
    min_width = min(i.width for i in images)

    total_height = 0
    for idx in range(len(images)):
        img = images[idx]

        if img.width > min_width:
            images[idx] = img.resize((min_width, int(img.height / img.width * min_width)), Image.ANTIALIAS)

        total_height += images[idx].height

    merged = Image.new('RGB', (min_width, total_height))
    offset = 0
    for img in images:
        merged.paste(img, (0, offset))
        offset += img.height

    return merged
