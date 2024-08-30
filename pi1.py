import unittest

""" The library to read and write PI1 files.

Supports only low resolution images (which PI1 are).
Doesn't support the data after the image data in the file.
Is rather sensitive to errors. 
"""


def read_pi1_palette(byte_array):
    palette = []
    for i in range(16):
        b = (byte_array[i * 2 + 1] & 0b111) << 5
        g = ((byte_array[i * 2 + 1] & 0b1110000) >> 4) << 5
        r = ((byte_array[i * 2] & 0b111) >> 0) << 5
        palette.append((r, g, b))
    return palette


def write_pi1_palette(palette):
    """ Write a 16 entry palette to a byte array that can be written to a PI1 file """
    byte_array = bytearray()
    for color in palette:
        r, g, b = color
        byte_array.append(r >> 5)
        byte_array.append(((g >> 5) << 4) + (b >> 5))
    return byte_array


def read_pi1_image(byte_array):
    image = []
    for i in range(0, 32000, 8):
        plane_0 = two_bytes_to_bit_iterator(byte_array[i], byte_array[i + 1])
        plane_1 = two_bytes_to_bit_iterator(byte_array[i + 2], byte_array[i + 3])
        plane_2 = two_bytes_to_bit_iterator(byte_array[i + 4], byte_array[i + 5])
        plane_3 = two_bytes_to_bit_iterator(byte_array[i + 6], byte_array[i + 7])

        for zip_palette_index in zip(plane_0, plane_1, plane_2, plane_3):
            # Convert the (a, b, c, d) tuple to a 4 bit index
            palette_index = (zip_palette_index[0]
                             + (zip_palette_index[1] << 1)
                             + (zip_palette_index[2] << 2)
                             + (zip_palette_index[3] << 3))

            image.append(palette_index)
    return image


def write_pi1_image(image):
    byte_array = bytearray()
    for i in range(0, 320 * 200, 16):
        planes = [0, 0, 0, 0]
        for j in range(16):
            palette_index = image[i + j]
            planes[0] = planes[0] << 1 | (palette_index & 1)
            planes[1] = planes[1] << 1 | ((palette_index >> 1) & 1)
            planes[2] = planes[2] << 1 | ((palette_index >> 2) & 1)
            planes[3] = planes[3] << 1 | ((palette_index >> 3) & 1)

        for plane in planes:
            byte_array.append((plane >> 8) & 0xFF)
            byte_array.append(plane & 0xFF)

    return byte_array


def two_bytes_to_bit_iterator(byte_1, byte_2):
    word = (byte_1 << 8) + byte_2
    for i in range(16):
        yield (word >> (15 - i)) & 1


class TestPI1(unittest.TestCase):
    def test_read_pi1_palette(self):
        byte_array = bytearray(b'\xff\xff' * 16)
        palette = read_pi1_palette(byte_array)
        self.assertEqual(palette, [(224, 224, 224)] * 16)

    def test_write_and_read_pi1_palette(self):
        palette = [(224, 224, 224)] * 16
        byte_array = write_pi1_palette(palette)
        self.assertEqual(read_pi1_palette(byte_array), palette)

    def read_pi1_image(self):
        byte_array = bytearray(b'\xff\xff' * 32000)
        image = read_pi1_image(byte_array)
        self.assertEqual(image, [15] * 320 * 200)

    def test_write_and_read_pi1_image(self):
        image = [15] * 320 * 200
        byte_array = write_pi1_image(image)
        self.assertEqual(32000, len(byte_array))
        self.assertEqual(read_pi1_image(byte_array), image)

    def test_write_and_read_pi1_image_other(self):
        image = [0, 10, 8, 15] * (320 * 200 // 4)
        byte_array = write_pi1_image(image)
        self.assertEqual(32000, len(byte_array))
        self.assertEqual(read_pi1_image(byte_array), image)
