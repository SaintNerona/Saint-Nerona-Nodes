import importlib.util
import tempfile
import unittest
from pathlib import Path

import torch


MODULE_PATH = Path(__file__).resolve().parents[1] / "h3_av_latent_loader.py"
SPEC = importlib.util.spec_from_file_location(
    "saint_nerona_h3_av_latent_loader", MODULE_PATH
)
H3_AV_LOADER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(H3_AV_LOADER)


class H3AVLatentLoaderTests(unittest.TestCase):
    def test_resolves_relative_path_against_output_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            checkpoint = Path(directory) / "shots" / "clip.safetensors"
            checkpoint.parent.mkdir()
            checkpoint.touch()

            resolved = H3_AV_LOADER.resolve_latent_path(
                "shots/clip.safetensors", directory
            )

            self.assertEqual(resolved, str(checkpoint.resolve()))

    def test_rejects_non_safetensors_path(self):
        with tempfile.TemporaryDirectory() as directory:
            checkpoint = Path(directory) / "clip.pt"
            checkpoint.touch()

            with self.assertRaisesRegex(ValueError, "safetensors"):
                H3_AV_LOADER.resolve_latent_path(str(checkpoint), directory)

    def test_accepts_joint_h3_tensor_shapes(self):
        video = torch.zeros((1, 24, 32, 38, 66))
        audio = torch.zeros((1, 32, 2, 178))

        result = H3_AV_LOADER.validate_h3_av_tensors(
            {"video": video, "audio": audio}
        )

        self.assertIs(result[0], video)
        self.assertIs(result[1], audio)

    def test_rejects_missing_audio_stream(self):
        video = torch.zeros((1, 24, 32, 38, 66))

        with self.assertRaisesRegex(ValueError, "video.*audio"):
            H3_AV_LOADER.validate_h3_av_tensors({"video": video})

    def test_rejects_invalid_audio_shape(self):
        video = torch.zeros((1, 24, 32, 38, 66))
        audio = torch.zeros((1, 32, 178))

        with self.assertRaisesRegex(ValueError, "audio latent"):
            H3_AV_LOADER.validate_h3_av_tensors(
                {"video": video, "audio": audio}
            )


if __name__ == "__main__":
    unittest.main()
