import importlib.util
import math
import sys
import types
import unittest
from pathlib import Path


class FakePreviewImage:
    OUTPUT_NODE = True

    def save_images(self, images, filename_prefix, prompt=None, extra_pnginfo=None):
        return {
            "ui": {"images": [{"filename": f"{filename_prefix}.png", "type": "temp"}]},
            "result": (images,),
        }


class FakeLoadImage:
    @classmethod
    def VALIDATE_INPUTS(cls, image):
        return True

    def load_image(self, image):
        return ({"loaded_from": image}, None)


NODES_MODULE = types.ModuleType("nodes")
NODES_MODULE.LoadImage = FakeLoadImage
NODES_MODULE.PreviewImage = FakePreviewImage
ORIGINAL_NODES_MODULE = sys.modules.get("nodes")
sys.modules["nodes"] = NODES_MODULE

MODULE_PATH = Path(__file__).resolve().parents[1] / "image_hold_nodes.py"
SPEC = importlib.util.spec_from_file_location("saint_nerona_image_hold_nodes", MODULE_PATH)
IMAGE_HOLD_NODES = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(IMAGE_HOLD_NODES)

if ORIGINAL_NODES_MODULE is None:
    del sys.modules["nodes"]
else:
    sys.modules["nodes"] = ORIGINAL_NODES_MODULE


class ImageHoldPreviewTests(unittest.TestCase):
    def test_image_input_is_optional(self):
        input_types = IMAGE_HOLD_NODES.SaintNeronaHoldImagePreview.INPUT_TYPES()

        self.assertNotIn("image", input_types.get("required", {}))
        self.assertIn("image", input_types["optional"])

    def test_returns_none_before_first_image(self):
        node = IMAGE_HOLD_NODES.SaintNeronaHoldImagePreview()

        result = node.hold_image()

        self.assertEqual(result["ui"]["images"], [])
        self.assertEqual(result["result"], (None,))

    def test_result_cache_is_disabled_for_held_state(self):
        self.assertTrue(math.isnan(IMAGE_HOLD_NODES.SaintNeronaHoldImagePreview.IS_CHANGED()))

    def test_holds_and_returns_the_same_image(self):
        node = IMAGE_HOLD_NODES.SaintNeronaHoldImagePreview()
        image = object()

        first_result = node.hold_image(image)
        held_result = node.hold_image()

        self.assertIs(first_result["result"][0], image)
        self.assertIs(held_result["result"][0], image)
        self.assertEqual(held_result["ui"]["images"][0]["type"], "temp")

    def test_loads_a_new_pasted_image(self):
        node = IMAGE_HOLD_NODES.SaintNeronaHoldImagePreview()

        result = node.hold_image(pasted_image="Saint-Nerona-Nodes/pasted.png")

        self.assertEqual(result["result"][0], {"loaded_from": "Saint-Nerona-Nodes/pasted.png"})

    def test_connected_image_has_priority_over_an_old_paste(self):
        node = IMAGE_HOLD_NODES.SaintNeronaHoldImagePreview()
        node.hold_image(pasted_image="Saint-Nerona-Nodes/pasted.png")
        connected_image = object()

        node.hold_image(connected_image, pasted_image="Saint-Nerona-Nodes/pasted.png")
        result = node.hold_image(pasted_image="Saint-Nerona-Nodes/pasted.png")

        self.assertIs(result["result"][0], connected_image)


if __name__ == "__main__":
    unittest.main()
