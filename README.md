# Saint Nerona Nodes

A focused collection of ComfyUI utility nodes for frame-accurate MiniMax H3
music-video workflows and everyday image handling.

## Included Nodes

| Node | Category | Purpose |
| --- | --- | --- |
| `(Saint Nerona) H3 Shot Timing` | `Saint Nerona/Audio` | Places a shot on a shared frame timeline and calculates a valid H3 generation length. |
| `(Saint Nerona) Audio Segment by Frames` | `Saint Nerona/Audio` | Slices ComfyUI audio at exact video-frame boundaries. |
| `(Saint Nerona) H3 Decoded Music Video Streamer` | `Saint Nerona/H3` | Assembles contiguous H3 continuation clips while retaining audio decoded from their sampled H3 AV latents. |
| `(Saint Nerona) H3 AV Latent Loader` | `Saint Nerona/H3` | Reloads an archived joint H3 checkpoint in the form required by the video and audio VAE decoders. |
| `(Saint Nerona) Image Megapixel Size` | `Saint Nerona/Image` | Calculates dimensions from an image aspect ratio, target megapixels, and a required multiple. |
| `(Saint Nerona) Hold Image Preview` | `Saint Nerona/Image` | Previews, stores, and passes through an optional image. |

## H3 Shot Timing

Defines one shot on a shared frame timeline and calculates the smallest valid
MiniMax H3 generation length (`5 + 17n`) that covers the requested final frame
count.

Use its outputs as a single timing source for:

- selecting the matching part of a master audio track;
- setting the H3 generation length;
- trimming the generated video and decoded audio;
- placing consecutive shots without cumulative timing drift.

For example, 120 output frames are exactly 5 seconds at 24 fps. H3 requires 124
generation frames for that range, so the four extra frames can be removed before
export.

## Audio Segment by Frames

Slices a standard ComfyUI `AUDIO` object using video-frame boundaries. Adjacent
segments calculate the same integer sample at their shared boundary, avoiding
one-sample gaps or overlaps caused by independently rounded time values.

For H3 custom-audio masking, place this node before `VAEEncodeAudio`. The final
video should still receive audio decoded from the sampled H3 latent rather than
the original source segment.

The optional silence padding is useful when an H3-valid generation range extends
slightly beyond the end of the source audio.

## H3 Decoded Music Video Streamer

Assembles a contiguous fixed-song MiniMax H3 continuation with an explicit final
audio path:

- inputs are sampled joint H3 video/audio latents only;
- there is no source-master `AUDIO` input;
- every configured `clip_1...clip_N` socket must be connected without a gap;
- Clip 1 becomes the generated starter and later clips become ordered MultiRef
  AV extensions;
- MultiRef decodes one video clip at a time, conforms H3-decoded audio to the
  exact frame timeline, replaces protected continuation overlaps at absolute
  sample boundaries, and performs one final VideoHelperSuite encode.

Set `input_count`, click **Update inputs**, and connect the sampled clips in their
exact song-timeline order. The initial recommended seam settings are 39 protected
context frames and up to 39 visual-overlap frames at 24 fps.

### Streamer Dependencies

The streamer requires:

- [ComfyUI-H3-Motion-Context-MultiRef](https://github.com/seitanism/ComfyUI-H3-Motion-Context-MultiRef), tested at `a823ca7d094e9982b031d5a7e33bb2f4f316aec3`;
- [ComfyUI-VideoHelperSuite](https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite), used by MultiRef for the final encode;
- matching MiniMax H3 video and audio VAEs.

The other Saint Nerona nodes do not require additional Python packages beyond
the ComfyUI environment.

### Continuation Checkpoints

The streamer itself does not save latent checkpoints. During one live graph
execution, sampled AV latents can pass directly from one clip to the next.

To continue an accepted clip after restarting ComfyUI or clearing the cache, use
MultiRef's `H3 Motion Context Save Latent` and `Load Latent` nodes on the sampled
joint AV latent:

- set `clip_index = 0` for automatically numbered archive files while comparing
  attempts;
- give each planned shot a stable prefix such as `shot_03`;
- load an accepted attempt by its exact file path rather than selecting the
  newest file in a directory;
- use a fixed positive `clip_index` only when a stable overwriteable chain slot
  is preferable to an attempt archive.

## H3 AV Latent Loader

Reloads an exact `.safetensors` checkpoint created from a sampled joint MiniMax
H3 video/audio latent. Unlike a continuation-only loader, its output is packed
as ComfyUI's decodable H3 `NestedTensor`, so it can connect directly to both
`VAEDecode` and `VAEDecodeAudio`.

Use an absolute checkpoint path or a path relative to `ComfyUI/output`. This is
useful for recovering full generated handles, auditing H3-decoded audio, or
re-exporting an accepted latent without rerunning diffusion. The node does not
modify the checkpoint and does not accept video-only or audio-only files.

## Image Megapixel Size

Calculates `width` and `height` from the input image aspect ratio and a target
megapixel count. Both dimensions are rounded to the selected multiple.

Inputs:

- `image` — the source image whose aspect ratio is preserved;
- `megapixels` — the target image area in millions of pixels;
- `divisible_by` — `1`, `8`, `16`, `32`, `64`, or `128`.

Because both dimensions are aligned to whole multiples, the final pixel count may
differ slightly from the requested value.

Typical choices:

- `8` works for many VAEs;
- `16` is useful for models with additional latent downsampling;
- `32`, `64`, or `128` should be used when required by a specific model;
- `1` disables dimension alignment.

## Hold Image Preview

Previews an image and returns the same tensor unchanged. Its `image` input is
optional.

- With a connected image, the node updates its preview and holds that image.
- Without a connected input, it returns the last image it received.
- When the node is selected, an image can be pasted with `Ctrl+V` or `Cmd+V`.
- Before receiving its first image, the output is `None`.
- A connected image remains in memory until the node instance is removed or
  ComfyUI is restarted.

Images received through the input socket are not saved. Clipboard images are
uploaded to `ComfyUI/input/Saint-Nerona-Nodes` so they can be restored with the
workflow. The preview uses ComfyUI's standard temporary PNG output.

## Installation

Clone the repository into `ComfyUI/custom_nodes`:

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/SaintNerona/Saint-Nerona-Nodes.git
```

Install the streamer dependencies listed above if that node will be used, then
restart ComfyUI. The nodes appear in the `Saint Nerona` categories.

## Tests

Run the focused unit tests from the repository directory with the Python
environment used by ComfyUI:

```bash
python -m unittest discover -s tests
```

## License

Saint Nerona Nodes is licensed under the GNU General Public License v3.0. See
[`LICENSE`](LICENSE). Third-party attribution for the MultiRef-backed H3 streamer
is recorded in [`NOTICE.md`](NOTICE.md).
