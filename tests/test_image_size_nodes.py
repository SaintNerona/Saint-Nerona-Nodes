import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "image_size_nodes.py"
SPEC = importlib.util.spec_from_file_location("saint_nerona_image_size_nodes", MODULE_PATH)
IMAGE_SIZE_NODES = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(IMAGE_SIZE_NODES)


class FakeImage:
    def __init__(self, width, height):
        self.shape = (1, height, width, 3)


class ImageMegapixelSizeTests(unittest.TestCase):
    def test_landscape_size_is_aligned_and_near_target(self):
        node = IMAGE_SIZE_NODES.SaintNeronaImageMegapixelSize()
        width, height = node.calculate_size(FakeImage(1920, 1080), 1.0, "8")

        self.assertEqual(width % 8, 0)
        self.assertEqual(height % 8, 0)
        self.assertLess(abs(width * height - 1_000_000) / 1_000_000, 0.05)
        self.assertLess(abs(width / height - 16 / 9) / (16 / 9), 0.01)

    def test_portrait_orientation_is_preserved(self):
        width, height = IMAGE_SIZE_NODES.calculate_megapixel_size(1080, 1920, 1.0, 32)

        self.assertLess(width, height)
        self.assertEqual(width % 32, 0)
        self.assertEqual(height % 32, 0)

    def test_square_size_uses_nearest_aligned_area(self):
        width, height = IMAGE_SIZE_NODES.calculate_megapixel_size(1024, 1024, 1.0, 64)

        self.assertEqual((width, height), (1024, 1024))


if __name__ == "__main__":
    unittest.main()
