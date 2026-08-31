import math


DIVISIBLE_BY_VALUES = ["1", "8", "16", "32", "64", "128"]


def _aligned_candidates(value, multiple):
    lower = max(multiple, int(math.floor(value / multiple)) * multiple)
    upper = max(multiple, int(math.ceil(value / multiple)) * multiple)
    return {lower, upper}


def calculate_megapixel_size(source_width, source_height, megapixels, divisible_by):
    target_pixels = float(megapixels) * 1_000_000
    source_ratio = source_width / source_height
    base_width = math.sqrt(target_pixels * source_ratio)
    base_height = math.sqrt(target_pixels / source_ratio)

    width_candidates = _aligned_candidates(base_width, divisible_by)
    height_candidates = _aligned_candidates(base_height, divisible_by)
    candidates = set()

    for width in width_candidates:
        for height in _aligned_candidates(width / source_ratio, divisible_by):
            candidates.add((width, height))

    for height in height_candidates:
        for width in _aligned_candidates(height * source_ratio, divisible_by):
            candidates.add((width, height))

    def candidate_score(size):
        width, height = size
        ratio_error = abs(width / height - source_ratio) / source_ratio
        pixel_error = abs(width * height - target_pixels) / target_pixels
        dimension_error = abs(width - base_width) / base_width + abs(height - base_height) / base_height
        return ratio_error, pixel_error, dimension_error

    return min(candidates, key=candidate_score)


class SaintNeronaImageMegapixelSize:
    DESCRIPTION = (
        "Calculates width and height from the input image aspect ratio and a target megapixel count. "
        "The result is rounded to the selected multiple."
    )

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE", {"tooltip": "Image whose aspect ratio will be preserved."}),
                "megapixels": ("FLOAT", {
                    "default": 1.0,
                    "min": 0.01,
                    "max": 64.0,
                    "step": 0.01,
                    "tooltip": "Target total image size in millions of pixels.",
                }),
                "divisible_by": (DIVISIBLE_BY_VALUES, {
                    "default": "8",
                    "tooltip": "Make both output dimensions divisible by this value.",
                }),
            },
        }

    RETURN_TYPES = ("INT", "INT")
    RETURN_NAMES = ("width", "height")
    OUTPUT_TOOLTIPS = ("Calculated width in pixels.", "Calculated height in pixels.")
    FUNCTION = "calculate_size"
    CATEGORY = "Saint Nerona/Image"

    def calculate_size(self, image, megapixels, divisible_by):
        _, source_height, source_width, _ = image.shape
        return calculate_megapixel_size(
            int(source_width),
            int(source_height),
            float(megapixels),
            int(divisible_by),
        )


NODE_CLASS_MAPPINGS = {
    "SaintNeronaImageMegapixelSize": SaintNeronaImageMegapixelSize,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SaintNeronaImageMegapixelSize": "(Saint Nerona) Image Megapixel Size",
}
