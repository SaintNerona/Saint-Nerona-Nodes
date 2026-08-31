import importlib.util
import sys
import types
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "h3_decoded_music_streamer.py"
SPEC = importlib.util.spec_from_file_location(
    "saint_nerona_h3_decoded_music_streamer", MODULE_PATH
)
STREAMER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(STREAMER)


class FakeMultiRefStreamer:
    calls = []

    def stream_to_vhs(
        self,
        video_vae,
        audio_vae,
        start_mode,
        input_count,
        context_frames,
        video_overlap_frames,
        source_fps,
        crop,
        filename_prefix,
        pix_fmt,
        crf,
        save_metadata,
        trim_to_audio,
        save_output,
        source_frames=None,
        source_audio=None,
        starter_latent=None,
        preview_gate=None,
        active_extensions=None,
        prompt=None,
        extra_pnginfo=None,
        unique_id=None,
        **kwargs,
    ):
        payload = locals().copy()
        payload.pop("self")
        self.calls.append(payload)
        return {"ui": {"gifs": []}, "result": (["decoded.mp4"],)}


class H3DecodedMusicVideoStreamerTests(unittest.TestCase):
    def setUp(self):
        self.previous_nodes = sys.modules.get("nodes")
        fake_nodes = types.ModuleType("nodes")
        fake_nodes.NODE_CLASS_MAPPINGS = {
            STREAMER.MULTIREF_STREAMER_ID: FakeMultiRefStreamer,
        }
        sys.modules["nodes"] = fake_nodes
        FakeMultiRefStreamer.calls.clear()

    def tearDown(self):
        if self.previous_nodes is None:
            sys.modules.pop("nodes", None)
        else:
            sys.modules["nodes"] = self.previous_nodes

    def test_schema_has_no_source_audio_route_and_exposes_dynamic_latents(self):
        schema = STREAMER.SaintNeronaH3DecodedMusicVideoStreamer.INPUT_TYPES()

        self.assertIn("video_vae", schema["required"])
        self.assertIn("audio_vae", schema["required"])
        self.assertNotIn("master_audio", schema["required"])
        self.assertNotIn("source_audio", schema["required"])
        self.assertEqual(schema["required"]["input_count"][1]["min"], 2)
        self.assertEqual(schema["optional"]["clip_1"][0], "LATENT")
        self.assertTrue(schema["optional"]["clip_1"][1]["lazy"])
        self.assertEqual(schema["optional"]["clip_64"][0], "LATENT")

    def test_delegates_contiguous_clips_to_generated_start_av_streamer(self):
        node = STREAMER.SaintNeronaH3DecodedMusicVideoStreamer()
        clips = [object(), object(), object()]
        result = node.stream_to_vhs(
            video_vae="video-vae",
            audio_vae="audio-vae",
            input_count=3,
            context_frames=39,
            video_overlap_frames=22,
            filename_prefix="video/test",
            pix_fmt="yuv420p",
            crf=18,
            save_metadata=True,
            trim_to_audio=True,
            save_output=True,
            preview_gate=["preview"],
            prompt={"graph": True},
            extra_pnginfo={"workflow": True},
            unique_id="node-7",
            clip_1=clips[0],
            clip_2=clips[1],
            clip_3=clips[2],
        )

        self.assertEqual(result["result"], (["decoded.mp4"],))
        self.assertEqual(len(FakeMultiRefStreamer.calls), 1)
        call = FakeMultiRefStreamer.calls[0]
        self.assertEqual(call["start_mode"], "t2v")
        self.assertEqual(call["input_count"], 2)
        self.assertEqual(call["active_extensions"], 2)
        self.assertIs(call["starter_latent"], clips[0])
        self.assertIs(call["kwargs"]["extension_1"], clips[1])
        self.assertIs(call["kwargs"]["extension_2"], clips[2])
        self.assertIsNone(call["source_frames"])
        self.assertIsNone(call["source_audio"])
        self.assertEqual(call["context_frames"], 39)
        self.assertEqual(call["video_overlap_frames"], 22)

    def test_rejects_a_middle_or_trailing_timeline_gap(self):
        node = STREAMER.SaintNeronaH3DecodedMusicVideoStreamer()

        with self.assertRaisesRegex(ValueError, "missing clip_2"):
            node.stream_to_vhs(
                video_vae=object(),
                audio_vae=object(),
                input_count=3,
                clip_1=object(),
                clip_3=object(),
            )

    def test_lazy_order_waits_for_preview_then_requests_active_clips(self):
        node = STREAMER.SaintNeronaH3DecodedMusicVideoStreamer()
        common = dict(
            video_vae=object(),
            audio_vae=object(),
            input_count=3,
            context_frames=39,
            video_overlap_frames=39,
            filename_prefix="video/test",
            pix_fmt="yuv420p",
            crf=19,
            save_metadata=True,
            trim_to_audio=True,
            save_output=True,
            preview_gate=None,
            clip_1=None,
            clip_2=None,
            clip_3=None,
        )

        self.assertEqual(node.check_lazy_status(**common), ["preview_gate"])
        common["preview_gate"] = ["ready"]
        self.assertEqual(
            node.check_lazy_status(**common),
            ["clip_1", "clip_2", "clip_3"],
        )

    def test_missing_multiref_dependency_fails_with_install_guidance(self):
        sys.modules["nodes"].NODE_CLASS_MAPPINGS = {}

        with self.assertRaisesRegex(RuntimeError, "MultiRef is required"):
            STREAMER._resolve_multiref_streamer()

    def test_frontend_declares_the_same_class_and_clip_socket_prefix(self):
        source = (ROOT / "web" / "h3_decoded_music_streamer.js").read_text(
            encoding="utf-8"
        )

        self.assertIn("SaintNeronaH3DecodedMusicVideoStreamer", source)
        self.assertIn('const PREFIX = "clip_"', source)
        self.assertIn('"Update inputs"', source)
        self.assertIn("Math.max(2", source)


if __name__ == "__main__":
    unittest.main()
