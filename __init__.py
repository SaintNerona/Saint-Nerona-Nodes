from .audio_timing_nodes import SaintNeronaAudioSegmentByFrames, SaintNeronaH3ShotTiming
from .h3_decoded_music_streamer import SaintNeronaH3DecodedMusicVideoStreamer
from .image_hold_nodes import SaintNeronaHoldImagePreview
from .image_size_nodes import SaintNeronaImageMegapixelSize


NODE_CLASS_MAPPINGS = {
    "SaintNeronaH3ShotTiming": SaintNeronaH3ShotTiming,
    "SaintNeronaAudioSegmentByFrames": SaintNeronaAudioSegmentByFrames,
    "SaintNeronaH3DecodedMusicVideoStreamer": SaintNeronaH3DecodedMusicVideoStreamer,
    "SaintNeronaImageMegapixelSize": SaintNeronaImageMegapixelSize,
    "SaintNeronaHoldImagePreview": SaintNeronaHoldImagePreview,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SaintNeronaH3ShotTiming": "(Saint Nerona) H3 Shot Timing",
    "SaintNeronaAudioSegmentByFrames": "(Saint Nerona) Audio Segment by Frames",
    "SaintNeronaH3DecodedMusicVideoStreamer": "(Saint Nerona) H3 Decoded Music Video Streamer",
    "SaintNeronaImageMegapixelSize": "(Saint Nerona) Image Megapixel Size",
    "SaintNeronaHoldImagePreview": "(Saint Nerona) Hold Image Preview",
}

WEB_DIRECTORY = "./web"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
