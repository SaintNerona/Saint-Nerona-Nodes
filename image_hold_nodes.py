from nodes import LoadImage, PreviewImage


class SaintNeronaHoldImagePreview(PreviewImage):
    DESCRIPTION = (
        "Previews and passes through an optional image. The last received image remains available "
        "until the node instance is discarded or ComfyUI is restarted."
    )

    def __init__(self):
        super().__init__()
        self.held_image = None
        self.loaded_pasted_image = None

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "optional": {
                "image": ("IMAGE", {"tooltip": "Image to preview, hold, and pass through unchanged."}),
                "pasted_image": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "tooltip": "Internal path for an image pasted into the node.",
                }),
            },
            "hidden": {
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
            },
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    OUTPUT_TOOLTIPS = ("The current image, or None before the first image is received.",)
    FUNCTION = "hold_image"
    OUTPUT_NODE = True
    CATEGORY = "Saint Nerona/Image"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("NaN")

    def hold_image(self, image=None, pasted_image="", prompt=None, extra_pnginfo=None):
        if image is not None:
            self.held_image = image
            self.loaded_pasted_image = pasted_image
        elif pasted_image and pasted_image != self.loaded_pasted_image:
            validation = LoadImage.VALIDATE_INPUTS(pasted_image)
            if validation is not True:
                raise ValueError(validation)
            self.held_image = LoadImage().load_image(pasted_image)[0]
            self.loaded_pasted_image = pasted_image

        if self.held_image is None:
            return {"ui": {"images": []}, "result": (None,)}

        return self.save_images(
            self.held_image,
            filename_prefix="SaintNeronaHoldPreview",
            prompt=prompt,
            extra_pnginfo=extra_pnginfo,
        )
