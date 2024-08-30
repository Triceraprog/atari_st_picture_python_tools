import PIL.Image
import argparse

from pi1 import write_pi1_palette, write_pi1_image

""" Transform an PNG with a palette into a PI1 image.
 
 Usage:
    python png_to_pi1.py <filename.png> [-palette_from <palette.png>] [-linear]
    
    -palette_from: Use the palette from a reference image, useful to have multiple images with the same palette
    -linear: Output a tileset of 16x16 tiles image in a linear format, which means all bytes from one tile are contiguous
    
The palette is written to a file with .pal extension as a series a python tuples.

In linear mode, the output is a .lin file without header. A .pi1 file is also written with the same data for debugging
purposes.
 
 Sensitive to errors, not very robust, and not versatile in terms of tileset. Did just what I needed.
 
 """


def palette_as_tuple_generator(palette):
    return (palette[i:i + 3] for i in range(0, len(palette), 3))


def write_pi1(filename_pi1, palette, image):
    # Group palette elements by 3
    palette = list(palette_as_tuple_generator(palette))
    with open(filename_pi1, "wb") as f:
        f.write(b"\0\0")
        f.write(write_pi1_palette(palette))
        f.write(write_pi1_image(image.getdata()))


def find_color_index(palette, color):
    # Palette is a flat list logically grouped by 3, color is a 3-tuple
    color = list(color)
    for i in range(0, len(palette), 3):
        palette_color = palette[i:i + 3]
        if palette_color == color:
            return i


def convert_to_palette(source_img, reference_palette):
    palette_image = PIL.Image.new("P", (1, 1))
    palette_image.putpalette(reference_palette)

    source_img = source_img.convert("RGB")
    dest_image = source_img.quantize(palette=palette_image, dither=0, colors=16)
    return dest_image


def dump_palette(palette, filename):
    # Convert the palette into the format xxxxxbbbxgggxrrr as 16 16-bit integers, from the tuple generator
    generator = palette_as_tuple_generator(palette)
    palette = [(color[0] >> 5) | ((color[1] >> 5) << 4) | ((color[2] >> 5) << 8) for color in generator]

    # Write the palette to a file
    with open(filename.replace(".png", ".pal"), "w") as f:
        for color in palette:
            f.write(f"\t0x{color:04X},\n")


def img_to_linear(img):
    if img.getpalette() is None:
        raise "Image to linearize must be palettized"

    data = list(img.getdata())
    linear_data = []

    index = 0
    for y in range(0, 200 - 8, 16):
        for x in range(0, 320, 16):
            for sp_y in range(16):
                for sp_x in range(16):
                    linear_data.append(data[(y + sp_y) * 320 + x + sp_x])
                    # linear_data.append(index)
            index += 1

    # Complete to 64000 bytes with index 0
    linear_data += [0] * (64000 - len(linear_data))

    return bytes(linear_data)


def main():
    # Use argparse to read the filename
    parser = argparse.ArgumentParser(description='Write PI1 images from a PNG file')
    parser.add_argument('filename', type=str, help='The filename of the PNG image')
    parser.add_argument('-palette_from', type=str, help='The filename of the reference palette image')
    parser.add_argument('-linear', action='store_true', help='Output linear binary')

    args = parser.parse_args()
    filename = args.filename
    palette_from = args.palette_from
    linear = args.linear

    img = PIL.Image.open(filename)

    if palette_from is not None:
        reference_palette_img = PIL.Image.open(palette_from)
        palette = reference_palette_img.getpalette()[0:16 * 3]

        index_for_green = find_color_index(palette, (0, 255, 0))
        index_for_fuchsia = find_color_index(palette, (255, 0, 255))

        if index_for_green is None or index_for_green != 45:
            print(f"Index for green: {index_for_green}, Index for fuchsia: {index_for_fuchsia}")
            raise "Green color must be at index 15"
        if index_for_fuchsia is None or index_for_fuchsia != 0:
            print(f"Index for green: {index_for_green}, Index for fuchsia: {index_for_fuchsia}")
            raise "Fuchsia color must be at index 0"

        img = convert_to_palette(img, palette)

        dump_palette(palette, filename)
    else:
        palette = img.getpalette()[0:16 * 3]

    if linear:
        linear_data = img_to_linear(img)

        filename = filename.replace(".png", ".lin")
        with open(filename, "wb") as f:
            f.write(write_pi1_image(linear_data))

        filename = filename.replace(".lin", ".pi1")
        palette = list(palette_as_tuple_generator(palette))
        with open(filename, "wb") as f:
            f.write(b"\0\0")
            f.write(write_pi1_palette(palette))
            f.write(write_pi1_image(linear_data))
    else:
        filename = filename.replace(".png", ".pi1")
        write_pi1(filename, palette, img)


if __name__ == '__main__':
    main()
