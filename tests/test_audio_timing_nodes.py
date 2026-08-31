import importlib.util
import unittest
from pathlib import Path

import torch


MODULE_PATH = Path(__file__).resolve().parents[1] / "audio_timing_nodes.py"
SPEC = importlib.util.spec_from_file_location("saint_nerona_audio_timing_nodes", MODULE_PATH)
AUDIO_TIMING_NODES = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIO_TIMING_NODES)


class H3ShotTimingTests(unittest.TestCase):
    def test_generation_frames_follow_h3_grid(self):
        cases = {
            1: 5,
            5: 5,
            6: 22,
            73: 73,
            120: 124,
            124: 124,
            243: 243,
        }

        for output_frames, expected in cases.items():
            with self.subTest(output_frames=output_frames):
                self.assertEqual(
                    AUDIO_TIMING_NODES.calculate_h3_generation_frames(output_frames),
                    expected,
                )

    def test_five_second_shot_exposes_generation_handle(self):
        result = AUDIO_TIMING_NODES.SaintNeronaH3ShotTiming().calculate(240, 120, 24.0)

        self.assertEqual(result[:5], (124, 120, 240, 360, 24.0))
        self.assertAlmostEqual(result[5], 10.0)
        self.assertAlmostEqual(result[6], 5.0)
        self.assertAlmostEqual(result[7], 124 / 24)


class AudioSegmentByFramesTests(unittest.TestCase):
    def test_adjacent_segments_share_the_same_sample_boundary(self):
        first_end = AUDIO_TIMING_NODES.frame_boundary_to_sample(73, 44_100, 24.0)
        second_start = AUDIO_TIMING_NODES.frame_boundary_to_sample(73, 44_100, 24.0)
        combined_end = AUDIO_TIMING_NODES.frame_boundary_to_sample(146, 44_100, 24.0)

        self.assertEqual(first_end, second_start)
        self.assertEqual(first_end, 134_137)
        self.assertEqual(combined_end, 268_275)

    def test_slices_audio_at_frame_boundaries_and_preserves_metadata(self):
        waveform = torch.arange(48_000, dtype=torch.float32).reshape(1, 1, -1)
        audio = {"waveform": waveform, "sample_rate": 48_000, "source": "synthetic"}

        result, start, end, count, padded = AUDIO_TIMING_NODES.slice_audio_by_frames(
            audio,
            start_frame=12,
            frame_count=6,
            fps=24.0,
            pad_with_silence=False,
        )

        self.assertEqual((start, end, count, padded), (24_000, 36_000, 12_000, 0))
        self.assertEqual(result["source"], "synthetic")
        self.assertTrue(torch.equal(result["waveform"], waveform[..., 24_000:36_000]))

    def test_pads_a_short_final_handle_with_silence(self):
        waveform = torch.ones((1, 2, 1_000), dtype=torch.float32)
        audio = {"waveform": waveform, "sample_rate": 1_000}

        result, start, end, count, padded = AUDIO_TIMING_NODES.slice_audio_by_frames(
            audio,
            start_frame=20,
            frame_count=10,
            fps=24.0,
            pad_with_silence=True,
        )

        self.assertEqual(start, 833)
        self.assertEqual(end, 1_250)
        self.assertEqual(count, 417)
        self.assertEqual(padded, 250)
        self.assertEqual(result["waveform"].shape[-1], 417)
        self.assertTrue(torch.all(result["waveform"][..., 167:] == 0))

    def test_rejects_a_short_segment_when_padding_is_disabled(self):
        audio = {"waveform": torch.ones((1, 1, 100)), "sample_rate": 1_000}

        with self.assertRaisesRegex(ValueError, "input contains only"):
            AUDIO_TIMING_NODES.slice_audio_by_frames(
                audio,
                start_frame=0,
                frame_count=24,
                fps=24.0,
                pad_with_silence=False,
            )


if __name__ == "__main__":
    unittest.main()
