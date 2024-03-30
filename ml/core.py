import matplotlib.pyplot as plt
import fitz
import io
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path


def pdf_extract(file: Path):
    out = []

    pdf_file = fitz.open(file)
    # iterate over PDF pages
    for page_index in range(pdf_file.page_count):
        # get the page itself
        page = pdf_file[page_index]
        image_li = page.get_images()
        # printing number of images found in this page
        # page index starts from 0 hence adding 1 to its content
        if image_li:
            print(f"[+] Found a total of {len(image_li)} images in page {page_index +1}")
        else:
            print(f"[!] No images found on page {page_index +1}")
        for image_index, img in enumerate(page.get_images(), start=1):
            # get the XREF of the image
            xref = img[0]
            # extract the image bytes
            base_image = pdf_file.extract_image(xref)
            image_bytes = base_image["image"]
            # get the image extension
            image_ext = base_image["ext"]
            # load it to PIL
            image = Image.open(io.BytesIO(image_bytes))

            out.append(image)

    return out


def show_image(img):
    width, height = img.size

    t = img.info.get("dpi", None)
    dpi = 100.0 if t is None else max(t)
    figsize = width / dpi, height / dpi
    fig, ax = plt.subplots(figsize=figsize)
    ax.axis("off")

    # plt.axis("off")
    plt.imshow(img, cmap='gray' if img.mode == "L" else None, aspect='auto')
    # plt.subplots(left=0, right=1, top=0, bottom=0)
    plt.tight_layout(pad=0)
    plt.show()


def draw_word(word, font_path, font_size, height):
    font = ImageFont.truetype(font_path, font_size)

    # Calculate the width and height of the text to be rendered
    text_width, text_height = font.getsize(word)

    # Adjust font size to fit the fixed height if necessary
    while text_height > height:
        font_size -= 1
        font = ImageFont.truetype(font_path, font_size)
        text_width, text_height = font.getsize(word)

    # Create an image canvas with the calculated width and fixed height
    image = Image.new("L", (text_width, height), "white")
    draw = ImageDraw.Draw(image)

    # Draw the text onto the canvas
    draw.text((0, 0), word, fill="black", font=font)

    return image
