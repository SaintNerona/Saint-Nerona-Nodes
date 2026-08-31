from fractions import Fraction
import math

import torch


H3_MIN_FRAMES = 5
H3_FRAME_STEP = 17


def calculate_h3_generation_frames(output_frames):
    output_frames = int(output_frames)
    if output_frames < 1:
        raise ValueError("output_frames must be at least 1")
    if output_frames <= H3_MIN_FRAMES:
        return H3_MIN_FRAMES
    steps = math.ceil((output_frames - H3_MIN_FRAMES) / H3_FRAME_STEP)
    return H3_MIN_FRAMES + steps * H3_FRAME_STEP


def frame_boundary_to_sample(frame, sample_rate, fps):
    frame = int(frame)
    sample_rate = int(sample_rate)
    if frame < 0:
        raise ValueError("frame must not be negative")
    if sample_rate <= 0:
        raise ValueError("sample_rate must be positive")

    fps_fraction = Fraction(str(float(fps)))
    if fps_fraction <= 0:
        raise ValueError("fps must be positive")

    numerator = frame * sample_rate * fps_fraction.denominator
    return numerator // fps_fraction.numerator


def slice_audio_by_frames(audio, start_frame, frame_count, fps, pad_with_silence):
    if not isinstance(audio, dict) or "waveform" not in audio or "sample_rate" not in audio:
        raise ValueError("audio must be a ComfyUI AUDIO object")

    frame_count = int(frame_count)
    if frame_count < 1:
        raise ValueError("frame_count must be at least 1")

    waveform = audio["waveform"]
    sample_rate = int(audio["sample_rate"])
    start_sample = frame_boundary_to_sample(start_frame, sample_rate, fps)
    end_sample = frame_boundary_to_sample(int(start_frame) + frame_count, sample_rate, fps)
    sample_count = end_sample - start_sample
    available_samples = int(waveform.shape[-1])

    if start_sample >= available_samples:
        segment = waveform[..., :0]
    else:
        segment = waveform[..., start_sample:min(end_sample, available_samples)]

    padded_samples = sample_count - int(segment.shape[-1])
    if padded_samples > 0:
        if not pad_with_silence:
            raise ValueError(
                f"Requested audio segment ends at sample {end_sample}, "
                f"but the input contains only {available_samples} samples"
            )
        padding_shape = tuple(segment.shape[:-1]) + (padded_samples,)
        segment = segment.new_zeros(padding_shape) if segment.shape[-1] == 0 else torch.cat(
            (segment, segment.new_zeros(padding_shape)), dim=-1
        )

    result = audio.copy()
    result["waveform"] = segment
    return result, start_sample, end_sample, sample_count, max(0, padded_samples)


class SaintNeronaH3ShotTiming:
    DESCRIPTION = (
        "Defines one shot on a shared video-frame timeline and calculates the smallest valid "
        "MiniMax H3 generation length (5 + 17n) that covers the requested output frames."
    )

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "timeline_start_frame": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 1_000_000,
                    "step": 1,
                    "tooltip": "Inclusive shot start on the final shared timeline.",
                }),
                "output_frames": ("INT", {
                    "default": 120,
                    "min": 1,
                    "max": 3600,
                    "step": 1,
                    "tooltip": "Frames retained in the final edit. At 24 fps, 120 frames is 5 seconds.",
                }),
                "fps": ("FLOAT", {
                    "default": 24.0,
                    "min": 1.0,
                    "max": 240.0,
                    "step": 0.001,
                    "tooltip": "Shared generation and delivery frame rate.",
                }),
            },
        }

    RETURN_TYPES = ("INT", "INT", "INT", "INT", "FLOAT", "FLOAT", "FLOAT", "FLOAT")
    RETURN_NAMES = (
        "generation_frames",
        "output_frames",
        "start_frame",
        "end_frame",
        "fps",
        "start_seconds",
        "output_duration",
        "generation_duration",
    )
    OUTPUT_TOOLTIPS = (
        "Nearest valid H3 frame count at or above output_frames.",
        "Requested final frame count, passed through for trimming.",
        "Timeline start frame, passed through for audio slicing.",
        "Exclusive final timeline end frame.",
        "Frame rate, passed through to timing-sensitive nodes.",
        "Timeline start in seconds.",
        "Final retained shot duration in seconds.",
        "H3 generation duration including any look-ahead frames.",
    )
    FUNCTION = "calculate"
    CATEGORY = "Saint Nerona/Audio"

    def calculate(self, timeline_start_frame, output_frames, fps):
        generation_frames = calculate_h3_generation_frames(output_frames)
        start_frame = int(timeline_start_frame)
        output_frames = int(output_frames)
        fps = float(fps)
        if fps <= 0:
            raise ValueError("fps must be positive")
        return (
            generation_frames,
            output_frames,
            start_frame,
            start_frame + output_frames,
            fps,
            start_frame / fps,
            output_frames / fps,
            generation_frames / fps,
        )


class SaintNeronaAudioSegmentByFrames:
    DESCRIPTION = (
        "Slices a ComfyUI AUDIO object using shared video-frame boundaries. Adjacent segments use "
        "the same integer sample boundary, avoiding cumulative gaps or overlaps from rounded seconds."
    )

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "audio": ("AUDIO", {
                    "tooltip": "Master audio before H3, or decoded H3 audio when trimming the output."
                }),
                "start_frame": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 1_000_000,
                    "step": 1,
                    "tooltip": "Inclusive start frame on the relevant timeline.",
                }),
                "frame_count": ("INT", {
                    "default": 120,
                    "min": 1,
                    "max": 3600,
                    "step": 1,
                    "tooltip": "Number of video frames represented by the returned audio.",
                }),
                "fps": ("FLOAT", {
                    "default": 24.0,
                    "min": 1.0,
                    "max": 240.0,
                    "step": 0.001,
                    "tooltip": "Frame rate used to convert frame boundaries into sample boundaries.",
                }),
                "pad_with_silence": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "Pad a short final generation handle with silence instead of failing.",
                }),
            },
        }

    RETURN_TYPES = ("AUDIO", "INT", "INT", "INT", "INT")
    RETURN_NAMES = ("audio", "start_sample", "end_sample", "sample_count", "padded_samples")
    OUTPUT_TOOLTIPS = (
        "Frame-aligned audio segment.",
        "Inclusive source sample boundary.",
        "Exclusive source sample boundary.",
        "Exact returned sample count.",
        "Number of silence samples appended at the end.",
    )
    FUNCTION = "slice_audio"
    CATEGORY = "Saint Nerona/Audio"

    def slice_audio(self, audio, start_frame, frame_count, fps, pad_with_silence):
        return slice_audio_by_frames(audio, start_frame, frame_count, fps, pad_with_silence)


NODE_CLASS_MAPPINGS = {
    "SaintNeronaH3ShotTiming": SaintNeronaH3ShotTiming,
    "SaintNeronaAudioSegmentByFrames": SaintNeronaAudioSegmentByFrames,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SaintNeronaH3ShotTiming": "(Saint Nerona) H3 Shot Timing",
    "SaintNeronaAudioSegmentByFrames": "(Saint Nerona) Audio Segment by Frames",
}
