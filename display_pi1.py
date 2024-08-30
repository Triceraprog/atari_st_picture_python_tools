import PIL
import PIL.Image
import argparse

from pi1 import read_pi1_palette, read_pi1_image

""" Display a PI1 image.

Usage: python display_pi1.py filename.pi1
"""

def read_pi1(filename_pi1):
    with open(filename_pi1, "rb") as f:
        header = f.read(2)
        if header != b"\0\0":
            raise "Error: only LOW RES supported"

        palette = read_pi1_palette(f.read(32))
        flat_index_image = read_pi1_image(f.read(32000))

        img = PIL.Image.new("RGB", (320, 200))
        for index, palette_index in enumerate(flat_index_image):
            img.putpixel((index % 320, index // 320), palette[palette_index])

        img.show()


if __name__ == '__main__':
    # Use argparse to read the filename
    parser = argparse.ArgumentParser(description='Display PI1 images')
    parser.add_argument('filename', type=str, help='The filename of the PI1 image')
    args = parser.parse_args()
    filename = args.filename

    read_pi1(filename)
