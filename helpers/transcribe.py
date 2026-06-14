"""Transcribe a video using pluggable transcription backends.

Extracts mono 16kHz audio via ffmpeg, transcribes with configured backend
(ElevenLabs, Whisper, Faster-Whisper, or custom), writes normalized output
to <edit_dir>/transcripts/<video_stem>.json.

Cached: if the output file already exists, the transcription is skipped.

Set TRANSCRIBER_BACKEND env var to choose: 'elevenlabs', 'whisper', or
'faster-whisper'. Defaults to 'whisper' (local, open source, no API key needed).

Usage:
    python helpers/transcribe.py <video_path>
    python helpers/transcribe.py <video_path> --edit-dir /custom/edit
    python helpers/transcribe.py <video_path> --language en
    python helpers/transcribe.py <video_path> --num-speakers 2
    TRANSCRIBER_BACKEND=faster-whisper python helpers/transcribe.py <video_path>
    TRANSCRIBER_BACKEND=elevenlabs python helpers/transcribe.py <video_path>
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from transcribers import get_backend


def extract_audio(video_path: Path, dest: Path) -> None:
    cmd = [
        "ffmpeg", "-y", "-i", str(video_path),
        "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le",
        str(dest),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def transcribe_one(
    video: Path,
    edit_dir: Path,
    language: str | None = None,
    num_speakers: int | None = None,
    backend_name: str | None = None,
    verbose: bool = True,
) -> Path:
    """Transcribe a single video. Returns path to transcript JSON.

    Cached: returns existing path immediately if the transcript already exists.

    Args:
        video: Path to video file.
        edit_dir: Output directory for transcripts.
        language: Optional ISO language code.
        num_speakers: Optional hint for diarization.
        backend_name: Transcriber backend ('elevenlabs', 'whisper', 'faster-whisper').
                     If None, uses TRANSCRIBER_BACKEND env var or defaults to 'whisper'.
        verbose: Print progress.

    Returns:
        Path to saved transcript JSON.
    """
    transcripts_dir = edit_dir / "transcripts"
    transcripts_dir.mkdir(parents=True, exist_ok=True)
    out_path = transcripts_dir / f"{video.stem}.json"

    if out_path.exists():
        if verbose:
            print(f"cached: {out_path.name}")
        return out_path

    # Get transcription backend
    try:
        backend = get_backend(backend_name)
    except ValueError as e:
        sys.exit(f"Error: {e}")

    is_valid, err = backend.validate_setup()
    if not is_valid:
        sys.exit(f"Error: {err}")

    if verbose:
        print(f"  using {backend.backend_name()}")
        print(f"  extracting audio from {video.name}", flush=True)

    t0 = time.time()
    with tempfile.TemporaryDirectory() as tmp:
        audio = Path(tmp) / f"{video.stem}.wav"
        extract_audio(video, audio)
        payload = backend.transcribe(audio, language, num_speakers, verbose)

    out_path.write_text(json.dumps(payload, indent=2))
    dt = time.time() - t0

    if verbose:
        kb = out_path.stat().st_size / 1024
        print(f"  saved: {out_path.name} ({kb:.1f} KB) in {dt:.1f}s")
        if isinstance(payload, dict) and "words" in payload:
            print(f"    words: {len(payload['words'])}")

    return out_path


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Transcribe a video using pluggable backends (Whisper, ElevenLabs, Faster-Whisper)",
        epilog="Set TRANSCRIBER_BACKEND env var to choose backend: 'whisper' (default), 'elevenlabs', 'faster-whisper'",
    )
    ap.add_argument("video", type=Path, help="Path to video file")
    ap.add_argument(
        "--edit-dir",
        type=Path,
        default=None,
        help="Edit output directory (default: <video_parent>/edit)",
    )
    ap.add_argument(
        "--language",
        type=str,
        default=None,
        help="Optional ISO language code (e.g., 'en'). Omit to auto-detect.",
    )
    ap.add_argument(
        "--num-speakers",
        type=int,
        default=None,
        help="Optional number of speakers when known. Improves diarization accuracy.",
    )
    ap.add_argument(
        "--backend",
        type=str,
        default=None,
        help="Transcription backend: 'whisper', 'elevenlabs', or 'faster-whisper'. "
             "Default: read from TRANSCRIBER_BACKEND env var or 'whisper'.",
    )
    args = ap.parse_args()

    video = args.video.resolve()
    if not video.exists():
        sys.exit(f"video not found: {video}")

    edit_dir = (args.edit_dir or (video.parent / "edit")).resolve()

    transcribe_one(
        video=video,
        edit_dir=edit_dir,
        language=args.language,
        num_speakers=args.num_speakers,
        backend_name=args.backend,
    )


if __name__ == "__main__":
    main()
