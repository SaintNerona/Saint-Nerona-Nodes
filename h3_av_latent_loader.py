import os


def resolve_latent_path(latent_path, output_directory):
    value = str(latent_path).strip()
    if not value:
        raise ValueError("latent_path must not be empty")

    expanded = os.path.expanduser(value)
    if not os.path.isabs(expanded):
        expanded = os.path.join(output_directory, expanded)
    resolved = os.path.realpath(expanded)

    if not resolved.lower().endswith(".safetensors"):
        raise ValueError("latent_path must point to a .safetensors file")
    if not os.path.isfile(resolved):
        raise FileNotFoundError(f"H3 AV latent does not exist: {resolved}")
    return resolved


def validate_h3_av_tensors(data):
    if "video" not in data or "audio" not in data:
        raise ValueError(
            "The checkpoint is not a saved H3 audiovisual latent: "
            "both 'video' and 'audio' tensors are required."
        )

    video = data["video"]
    audio = data["audio"]
    if getattr(video, "ndim", None) != 5:
        raise ValueError(
            "Expected H3 video latent [B,C,T,H,W], got "
            f"{tuple(getattr(video, 'shape', ())) }"
        )
    if getattr(audio, "ndim", None) != 4:
        raise ValueError(
            "Expected H3 audio latent [B,C,2,T], got "
            f"{tuple(getattr(audio, 'shape', ())) }"
        )
    if int(audio.shape[2]) != 2:
        raise ValueError(
            "Expected the H3 stereo axis to contain 2 channels, got "
            f"{int(audio.shape[2])}"
        )
    if int(video.shape[0]) != int(audio.shape[0]):
        raise ValueError("H3 video and audio latent batch sizes do not match")
    return video, audio


class SaintNeronaH3AVLatentLoader:
    """Load an archived joint H3 latent in the form expected by VAE decoders."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "latent_path": (
                    "STRING",
                    {
                        "default": "h3_checkpoints/shot_01_00001_.safetensors",
                        "multiline": False,
                        "tooltip": (
                            "Absolute path or path relative to ComfyUI/output. "
                            "Use a checkpoint saved from a sampled joint H3 AV latent."
                        ),
                    },
                )
            }
        }

    RETURN_TYPES = ("LATENT", "STRING")
    RETURN_NAMES = ("av_latent", "resolved_path")
    FUNCTION = "load"
    CATEGORY = "Saint Nerona/H3"
    DESCRIPTION = (
        "Loads a saved joint MiniMax H3 video/audio latent as a decodable "
        "NestedTensor for VAEDecode and VAEDecodeAudio."
    )

    @classmethod
    def IS_CHANGED(cls, latent_path):
        try:
            import folder_paths

            path = resolve_latent_path(
                latent_path, folder_paths.get_output_directory()
            )
            stat = os.stat(path)
            return f"{path}:{stat.st_mtime_ns}:{stat.st_size}"
        except Exception:
            return float("NaN")

    def load(self, latent_path):
        import comfy.nested_tensor
        import comfy.utils
        import folder_paths

        path = resolve_latent_path(
            latent_path, folder_paths.get_output_directory()
        )
        data = comfy.utils.load_torch_file(path, safe_load=True)
        video, audio = validate_h3_av_tensors(data)
        latent = {
            "samples": comfy.nested_tensor.NestedTensor((video, audio))
        }
        return latent, path
