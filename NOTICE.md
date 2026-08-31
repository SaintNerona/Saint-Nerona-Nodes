# Third-Party Notices

## H3 Motion Context MultiRef

`(Saint Nerona) H3 Decoded Music Video Streamer` delegates its low-memory
decoding, continuation-overlap assembly, and VideoHelperSuite output to:

- Project: `seitanism/ComfyUI-H3-Motion-Context-MultiRef`
- Reviewed revision: `a823ca7d094e9982b031d5a7e33bb2f4f316aec3`
- Source: https://github.com/seitanism/ComfyUI-H3-Motion-Context-MultiRef
- License: GNU General Public License v3.0

MultiRef is a modified fork of:

- Original project: `NikoDemon80/ComfyUI-H3-Motion-Context`
- Original author: NikoDemon80
- Source: https://github.com/NikoDemon80/ComfyUI-H3-Motion-Context
- License: GNU General Public License v3.0

The dynamic clip-socket behavior in `web/h3_decoded_music_streamer.js` was
adapted from MultiRef's dynamic streaming-input extension. Saint Nerona changes
the node identity, requires a contiguous fixed-song clip sequence, and exposes
only sampled H3 AV latent inputs—never a source-master audio input.
