# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Saint Nerona contributors

"""Strict fixed-song H3 final streamer backed by MultiRef's AV assembler.

The node deliberately exposes no source ``AUDIO`` input. Every final audio
sample must therefore originate in one of the sampled MiniMax H3 AV latents.
MultiRef owns the low-RAM video decode, exact audio-timebase conformance,
protected-overlap replacement, and final VideoHelperSuite encode. This wrapper
adds music-timeline semantics and rejects missing clips before delegating.
"""

from __future__ import annotations

import inspect


MULTIREF_STREAMER_ID = "MiniMaxH3StreamLiveExtensionAVToVHS"
MAX_CLIPS = 64
DEFAULT_CLIPS = 2


def _resolve_multiref_streamer():
    """Resolve the installed MultiRef node after all custom packs have loaded."""
    try:
        import nodes as comfy_nodes
    except Exception as exc:  # pragma: no cover - broken ComfyUI installation
        raise RuntimeError(
            "saint_nerona_h3_streamer: could not import ComfyUI's nodes module"
        ) from exc

    cls = getattr(comfy_nodes, "NODE_CLASS_MAPPINGS", {}).get(MULTIREF_STREAMER_ID)
    if cls is None:
        raise RuntimeError(
            "saint_nerona_h3_streamer: H3 Motion Context MultiRef is required. "
            "Install and enable ComfyUI-H3-Motion-Context-MultiRef, then restart "
            "ComfyUI."
        )

    method = getattr(cls, "stream_to_vhs", None)
    if not callable(method):
        raise RuntimeError(
            "saint_nerona_h3_streamer: the installed MultiRef AV streamer does "
            "not expose stream_to_vhs. Use the documented compatible MultiRef "
            "revision or update this wrapper."
        )

    # The wrapper intentionally targets the public ComfyUI node-call contract,
    # not MultiRef's private helper functions. Fail early with a useful message
    # if that contract changes at a pinned dependency boundary.
    try:
        parameters = inspect.signature(method).parameters
    except (TypeError, ValueError):
        parameters = {}
    required = {
        "video_vae",
        "audio_vae",
        "start_mode",
        "input_count",
        "context_frames",
        "video_overlap_frames",
        "starter_latent",
    }
    if parameters and not required.issubset(parameters):
        missing = sorted(required.difference(parameters))
        raise RuntimeError(
            "saint_nerona_h3_streamer: incompatible MultiRef AV streamer; "
            "missing parameters: " + ", ".join(missing)
        )
    return cls


def _vhs_inputs():
    return {
        "filename_prefix": (
            "STRING",
            {"default": "video/saint_nerona_h3_decoded_music_video"},
        ),
        "pix_fmt": (["yuv420p", "yuv420p10le"], {"default": "yuv420p"}),
        "crf": ("INT", {"default": 19, "min": 0, "max": 100, "step": 1}),
        "save_metadata": ("BOOLEAN", {"default": True}),
        "trim_to_audio": ("BOOLEAN", {"default": True}),
        "save_output": ("BOOLEAN", {"default": True}),
    }


class SaintNeronaH3DecodedMusicVideoStreamer:
    """Assemble a contiguous fixed-song continuation from sampled H3 AV clips."""

    MAX_CLIPS = MAX_CLIPS
    DEFAULT_CLIPS = DEFAULT_CLIPS

    @classmethod
    def INPUT_TYPES(cls):
        required = {
            "video_vae": (
                "VAE",
                {
                    "tooltip": (
                        "MiniMax H3 video VAE used to decode one clip at a time."
                    )
                },
            ),
            "audio_vae": (
                "VAE",
                {
                    "tooltip": (
                        "MiniMax H3 audio VAE. Final audio is decoded only from "
                        "the connected sampled H3 AV latents."
                    )
                },
            ),
            "input_count": (
                "INT",
                {
                    "default": cls.DEFAULT_CLIPS,
                    "min": 2,
                    "max": cls.MAX_CLIPS,
                    "step": 1,
                    "tooltip": (
                        "Total number of contiguous music clips, including Clip 1. "
                        "Set this value, then click Update inputs."
                    ),
                },
            ),
            "context_frames": (
                "INT",
                {
                    "default": 39,
                    "min": 39,
                    "max": 9999,
                    "step": 1,
                    "tooltip": (
                        "Protected continuation prefix. MultiRef snaps this to "
                        "an exact shared H3 video/audio boundary: 39, 90, 141, ..."
                    ),
                },
            ),
            "video_overlap_frames": (
                "INT",
                {
                    "default": 39,
                    "min": 0,
                    "max": 9999,
                    "step": 1,
                    "tooltip": (
                        "Linear visual blend within the protected prefix. Audio "
                        "uses exact continuation-owned sample replacement."
                    ),
                },
            ),
        }
        required.update(_vhs_inputs())

        optional = {
            "preview_gate": (
                "VHS_FILENAMES",
                {
                    "lazy": True,
                    "tooltip": (
                        "Optional execution-order gate from a completed clip preview."
                    ),
                },
            )
        }
        for i in range(1, cls.MAX_CLIPS + 1):
            optional[f"clip_{i}"] = (
                "LATENT",
                {
                    "lazy": True,
                    "tooltip": (
                        "Sampled MiniMax H3 joint video/audio latent. Clips must "
                        "be connected in exact song-timeline order with no gaps."
                    ),
                },
            )

        return {
            "required": required,
            "optional": optional,
            "hidden": {
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
                "unique_id": "UNIQUE_ID",
            },
        }

    RETURN_TYPES = ("VHS_FILENAMES",)
    RETURN_NAMES = ("filenames",)
    FUNCTION = "stream_to_vhs"
    OUTPUT_NODE = True
    CATEGORY = "Saint Nerona/H3"
    DESCRIPTION = (
        "Low-RAM final output for a contiguous MiniMax H3 fixed-song continuation. "
        "It accepts only sampled joint H3 AV latents, rejects missing timeline "
        "clips, and delegates sequential video decode plus exact H3-decoded audio "
        "assembly to MultiRef's AV streamer. No source-master AUDIO socket exists."
    )

    @classmethod
    def _count(cls, input_count):
        return max(2, min(cls.MAX_CLIPS, int(input_count)))

    @classmethod
    def _required_clip_names(cls, input_count):
        return [f"clip_{i}" for i in range(1, cls._count(input_count) + 1)]

    def check_lazy_status(
        self,
        video_vae,
        audio_vae,
        input_count,
        context_frames,
        video_overlap_frames,
        filename_prefix,
        pix_fmt,
        crf,
        save_metadata,
        trim_to_audio,
        save_output,
        **kwargs,
    ):
        if "preview_gate" in kwargs and kwargs["preview_gate"] is None:
            return ["preview_gate"]
        return [
            name
            for name in self._required_clip_names(input_count)
            if name in kwargs and kwargs[name] is None
        ]

    def stream_to_vhs(
        self,
        video_vae,
        audio_vae,
        input_count=DEFAULT_CLIPS,
        context_frames=39,
        video_overlap_frames=39,
        filename_prefix="video/saint_nerona_h3_decoded_music_video",
        pix_fmt="yuv420p",
        crf=19,
        save_metadata=True,
        trim_to_audio=True,
        save_output=True,
        preview_gate=None,
        prompt=None,
        extra_pnginfo=None,
        unique_id=None,
        **kwargs,
    ):
        count = self._count(input_count)
        names = self._required_clip_names(count)
        missing = [name for name in names if kwargs.get(name) is None]
        if missing:
            raise ValueError(
                "saint_nerona_h3_streamer: fixed-song clips must form one "
                f"contiguous sequence from clip_1 through clip_{count}; "
                f"missing {missing[0]}"
            )

        clips = [kwargs[name] for name in names]
        upstream_cls = _resolve_multiref_streamer()
        upstream = upstream_cls()
        extension_count = count - 1
        extension_inputs = {
            f"extension_{i}": clips[i]
            for i in range(1, count)
        }

        return upstream.stream_to_vhs(
            video_vae=video_vae,
            audio_vae=audio_vae,
            # MultiRef distinguishes only an uploaded existing-video start from
            # a generated H3 starter. "t2v" selects the latter; the latent may
            # itself have been produced through T2VA, I2VA, or REF2VA.
            start_mode="t2v",
            input_count=extension_count,
            context_frames=int(context_frames),
            video_overlap_frames=int(video_overlap_frames),
            source_fps=24.0,
            crop="disabled",
            filename_prefix=str(filename_prefix),
            pix_fmt=str(pix_fmt),
            crf=int(crf),
            save_metadata=bool(save_metadata),
            trim_to_audio=bool(trim_to_audio),
            save_output=bool(save_output),
            starter_latent=clips[0],
            preview_gate=preview_gate,
            active_extensions=extension_count,
            prompt=prompt,
            extra_pnginfo=extra_pnginfo,
            unique_id=unique_id,
            **extension_inputs,
        )


NODE_CLASS_MAPPINGS = {
    "SaintNeronaH3DecodedMusicVideoStreamer": (
        SaintNeronaH3DecodedMusicVideoStreamer
    ),
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SaintNeronaH3DecodedMusicVideoStreamer": (
        "(Saint Nerona) H3 Decoded Music Video Streamer"
    ),
}
