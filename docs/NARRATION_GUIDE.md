# Reproduce the English narration

The narration tells the same Friday-dinner story over the actual accepted
recording. It uses a stock synthetic voice, not Alexa or a clone of the
creator's voice. No music is added. All application frames remain in their
original order and at their original dimensions; only the 120px caption band
is replaced and an audio track is added. H.264 re-encoding changes bytes.

The [script and timings](narration.json) are public. The original source remains
unchanged at SHA-256
`95eeb6f2dea2a8dd3287eb91368a99f98b86398a94746a26fb21d289316c47bd`.
Its original SRT remains separately preserved. See
[publication history](VIDEO_PUBLICATION.md) for the accepted public recording.
The reviewed render was later accepted and published separately; that result
does not rewrite the original source or its publication history.

## Isolated authoring setup

Use a cloud Linux runner or equivalent with Python 3.12+, FFmpeg/ffprobe built
with libass, and DejaVu Sans. No AWS or speech-service credentials are used.
These dependencies are not installed in the application container.

```bash
python -m venv .media-venv
.media-venv/bin/pip install -r requirements-media.txt
mkdir -p model
```

Download only these public files from the pinned
[ONNX model revision](https://huggingface.co/onnx-community/Kokoro-82M-v1.0-ONNX/tree/1939ad2a8e416c0acfeecc08a694d14ef25f2231):

| Repository path | Save as | Expected SHA-256 |
| --- | --- | --- |
| onnx/model.onnx | model/onnx_model.onnx | 8fbea51ea711f2af382e88c833d9e288c6dc82ce5e98421ea61c058ce21a34cb |
| voices/af_heart.bin | model/voices_af_heart.bin | d583ccff3cdca2f7fae535cb998ac07e9fcb90f09737b9a41fa2734ec44a8f0b |

Then provide the preserved original MP4:

```bash
.media-venv/bin/python scripts/render_narration.py \
  /path/to/hestiarelay-candidate.mp4 model qa-artifacts/narrated
```

The renderer verifies source/model/voice checksums before inference. It refuses
an existing output directory, invalid dimensions/duration, overlapping scenes,
caption markup and speech that would exceed its scene. It creates an MP4,
English SRT/ASS, WAV narration, per-scene audio, encoder log and hash receipt.
All selected scenes fit at normal speed in the reviewed candidate. It never
uploads a file or changes the application.

Different CPU/runtime/FFmpeg versions can produce different bytes. Reproducible
steps do not promise bit-identical encoding across platforms. Check the new
receipt, full video, captions, pronunciation, stream duration and source-frame
similarity before accepting any render.

## Source and license notices

- [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M), by hexgrad:
  Apache-2.0 model release. The upstream model card describes training
  provenance and its acknowledgments, including Koniwa and SIWIS material.
- [ONNX Community conversion](https://huggingface.co/onnx-community/Kokoro-82M-v1.0-ONNX):
  Apache-2.0, pinned revision above; stock `af_heart` voice from that repository.
- [kokoro-onnx](https://github.com/thewh1teagle/kokoro-onnx), by thewh1teagle:
  MIT inference wrapper.
- ONNX Runtime: MIT. NumPy: BSD-3-Clause. SoundFile: BSD-3-Clause, with libsndfile
  under LGPL-2.1-or-later. Phonemizer and eSpeak NG have GPL licenses; these are
  separate authoring dependencies, not relicensed as part of HestiaRelay's MIT
  source. Keep their upstream licenses when redistributing their code/binaries.
- FFmpeg has LGPL/GPL build-dependent components; the authoring build uses
  libx264. DejaVu fonts retain their upstream font license. No third-party
  tool binary, model weight, voice embedding or font file is committed here.

These notices identify the tool and model provenance; they are not a universal
rights guarantee. The candidate has no claimed human narrator, celebrity voice,
live Alexa response or new AWS call. Final entrant rights declarations still
apply. Preserve the source notices with any redistributed authoring bundle.

## Acceptance and publication

Technical checks cover integrity, timings, non-clipping, stream formats,
loudness, frame similarity and caption visibility. The creator accepted the
exact candidate identified above and explicitly approved its publication. The
same file was uploaded once and YouTube confirmed it Public at
[the narrated demonstration](https://www.youtube.com/watch?v=NC2oy4x9Xdw).
See the [publication receipt](evidence/narrated-video-publication-20260914.json).
The accepted original remains preserved; its human playback result is not
transferred to this separate video.
