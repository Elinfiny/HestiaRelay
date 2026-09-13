"""Render a narrated candidate from the preserved recording, never publish it."""

import argparse
import hashlib
import json
import math
import subprocess
import textwrap
from pathlib import Path

MODEL_SHA = "8fbea51ea711f2af382e88c833d9e288c6dc82ce5e98421ea61c058ce21a34cb"
VOICE_SHA = "d583ccff3cdca2f7fae535cb998ac07e9fcb90f09737b9a41fa2734ec44a8f0b"


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def run(*args):
    return subprocess.run(args, check=True, capture_output=True, text=True)


def stamp(seconds, ass=False):
    scale = 100 if ass else 1000
    ticks = round(seconds * scale)
    whole, fraction = divmod(ticks, scale)
    hours, whole = divmod(whole, 3600)
    minutes, seconds = divmod(whole, 60)
    return (
        f"{hours}:{minutes:02}:{seconds:02}.{fraction:02}" if ass else
        f"{hours:02}:{minutes:02}:{seconds:02},{fraction:03}"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("model_dir", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--script", type=Path, default=Path("docs/narration.json"))
    args = parser.parse_args()
    script = json.loads(args.script.read_text())
    if digest(args.source) != script["source_video_sha256"]:
        raise ValueError("Source does not match the accepted original recording")
    model = args.model_dir / "onnx_model.onnx"
    voice = args.model_dir / "voices_af_heart.bin"
    if digest(model) != MODEL_SHA or digest(voice) != VOICE_SHA:
        raise ValueError("Model or stock voice checksum mismatch")
    duration = script["duration_seconds"]
    previous = 0
    for scene in script["scenes"]:
        if not 0 <= previous <= scene["start"] < scene["end"] <= duration:
            raise ValueError("Scene timings overlap or exceed the recording")
        if any(c in scene["text"] for c in "{}\\\n\r"):
            raise ValueError("Unsupported caption markup")
        previous = scene["end"]
    probe = json.loads(run(
        "ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json",
        str(args.source),
    ).stdout)
    video = next(s for s in probe["streams"] if s["codec_type"] == "video")
    if (video["width"], video["height"]) != (1440, 1120):
        raise ValueError("Expected the original 1440x1000 app and 120px caption band")
    if abs(float(probe["format"]["duration"]) - duration) > 0.05:
        raise ValueError("Unexpected source duration")
    if args.output.exists():
        raise FileExistsError("Use a new output directory; preserved candidates are immutable")
    args.output.mkdir(parents=True)

    import numpy as np
    import onnxruntime as rt
    import soundfile as sf
    from kokoro_onnx import Kokoro

    voices = args.output / "voices.npz"
    np.savez(voices, af_heart=np.fromfile(voice, dtype="<f4").reshape(-1, 1, 256))
    options = rt.SessionOptions()
    options.intra_op_num_threads = 2
    options.inter_op_num_threads = 1
    session = rt.InferenceSession(
        str(model), sess_options=options, providers=["CPUExecutionProvider"]
    )
    engine = Kokoro.from_session(session, str(voices))
    rate = 24000
    mix = np.zeros(round(duration * rate), dtype=np.float32)
    srt, subtitles, receipts = [], [], []
    for index, scene in enumerate(script["scenes"]):
        available = scene["end"] - scene["start"] - 0.25
        audio, sample_rate = engine.create(
            scene["text"], voice=script["voice"], speed=1.0, lang="en-us"
        )
        speed = 1.0
        if len(audio) / rate > available:
            speed = math.ceil((len(audio) / rate / available + 0.01) * 100) / 100
            if speed > 1.12:
                raise ValueError("Rewrite the scene; narration would be rushed")
            audio, sample_rate = engine.create(
                scene["text"], voice=script["voice"], speed=speed, lang="en-us"
            )
        if sample_rate != rate or len(audio) / rate > available:
            raise ValueError("Audio cannot fit its scene without clipping")
        start = round((scene["start"] + 0.1) * rate)
        mix[start:start + len(audio)] = audio
        sf.write(args.output / f"{index:02}.wav", audio, rate, subtype="PCM_16")
        readable = scene["text"].replace("M C P", "MCP").replace("H T T P", "HTTP")
        readable = readable.replace("Hestia Relay", "HestiaRelay")
        lines = textwrap.wrap(readable, 86)
        if len(lines) > 2:
            raise ValueError("Caption would exceed the two-line band")
        srt.append(
            f"{index + 1}\n{stamp(scene['start'])} --> {stamp(scene['end'])}\n"
            + "\n".join(lines) + "\n"
        )
        subtitles.append(
            f"Dialogue: 0,{stamp(scene['start'], True)},{stamp(scene['end'], True)},"
            "Default,,0,0,0,," + r"\N".join(lines)
        )
        receipts.append({
            "scene": index + 1, "start": start / rate,
            "audio_seconds": len(audio) / rate, "scene_end": scene["end"],
            "speed": speed, "clipped": False,
        })
        print(json.dumps(receipts[-1]), flush=True)
    sf.write(args.output / "narration.wav", mix, rate, subtype="PCM_16")
    (args.output / "captions.srt").write_text("\n".join(srt))
    (args.output / "captions.ass").write_text(
        "[Script Info]\nScriptType: v4.00+\nPlayResX: 1440\nPlayResY: 1120\n"
        "[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, "
        "SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, "
        "StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
        "Alignment, MarginL, MarginR, MarginV, Encoding\n"
        "Style: Default,DejaVu Sans,28,&H00FFFFFF,&H00FFFFFF,&H00172C24,"
        "&H00172C24,0,0,0,0,100,100,0,0,1,0,0,2,48,48,27,1\n"
        "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, "
        "MarginV, Effect, Text\n" + "\n".join(subtitles) + "\n"
    )
    # This changes only the lower caption band; all application frames stay in order.
    output = args.output.resolve()
    encoded = subprocess.run([
        "ffmpeg", "-nostdin", "-v", "info", "-i", str(args.source.resolve()),
        "-i", "narration.wav", "-map", "0:v:0", "-map", "1:a:0",
        "-vf", "crop=1440:1000:0:0,pad=1440:1120:0:0:0x172c24,ass=captions.ass",
        "-af", "loudnorm=I=-16:TP=-1.5:LRA=7:print_format=json",
        "-t", str(duration), "-c:v", "libx264", "-crf", "18", "-preset", "medium",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-ar", "48000",
        "-movflags", "+faststart", "hestiarelay-narrated.mp4",
    ], cwd=output, check=True, capture_output=True, text=True)
    (output / "encode.log").write_text(encoded.stderr)
    report = {
        "schema_version": 1, "status": "CANDIDATE_REQUIRES_FINAL_VISUAL_REVIEW",
        "source_sha256": digest(args.source), "script_sha256": digest(args.script),
        "model_sha256": MODEL_SHA, "voice_sha256": VOICE_SHA,
        "voice_kind": script["voice_kind"], "duration_seconds": duration,
        "application_frames": "Original order, dimensions and timing; re-encoded",
        "caption_band": "Original 120px band replaced with narration captions",
        "scenes": receipts,
        "files": {p.name: digest(p) for p in output.iterdir()
                  if p.suffix in {".mp4", ".srt", ".ass", ".wav"}},
        "publication": "Not uploaded; original public video unchanged",
    }
    (output / "render-report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"video": str(output / "hestiarelay-narrated.mp4")}), flush=True)


if __name__ == "__main__":
    main()
