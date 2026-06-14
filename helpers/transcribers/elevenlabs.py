"""ElevenLabs Scribe transcription backend."""

import os
import sys
from pathlib import Path

import requests

from .base import TranscriptionBackend


class ElevenLabsBackend(TranscriptionBackend):
    """Uses ElevenLabs Scribe API for transcription.

    Requires ELEVENLABS_API_KEY environment variable or .env file.
    Word-level timestamps, speaker diarization, and audio events included.
    """

    SCRIBE_URL = "https://api.elevenlabs.io/v1/speech-to-text"

    def __init__(self):
        self.api_key = self._load_api_key()

    def _load_api_key(self) -> str:
        """Load API key from .env or environment."""
        for candidate in [Path(".env"), Path(__file__).resolve().parent.parent.parent / ".env"]:
            if candidate.exists():
                for line in candidate.read_text().splitlines():
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    if k.strip() == "ELEVENLABS_API_KEY":
                        return v.strip().strip('"').strip("'")
        v = os.environ.get("ELEVENLABS_API_KEY", "")
        if not v:
            return None
        return v

    def validate_setup(self) -> tuple[bool, str]:
        """Check if API key is available."""
        if not self.api_key:
            return (
                False,
                "ELEVENLABS_API_KEY not found in .env or environment. "
                "Set it or use a different TRANSCRIBER_BACKEND.",
            )
        return True, ""

    def backend_name(self) -> str:
        """Return backend name."""
        return "ElevenLabs Scribe"

    def transcribe(
        self,
        audio_path: Path,
        language: str | None = None,
        num_speakers: int | None = None,
        verbose: bool = True,
    ) -> dict:
        """Transcribe with ElevenLabs Scribe."""
        is_valid, err = self.validate_setup()
        if not is_valid:
            raise RuntimeError(err)

        if verbose:
            size_mb = audio_path.stat().st_size / (1024 * 1024)
            print(f"  uploading to ElevenLabs ({size_mb:.1f} MB)", flush=True)

        data = {
            "model_id": "scribe_v1",
            "diarize": "true",
            "tag_audio_events": "true",
            "timestamps_granularity": "word",
        }
        if language:
            data["language_code"] = language
        if num_speakers:
            data["num_speakers"] = str(num_speakers)

        with open(audio_path, "rb") as f:
            resp = requests.post(
                self.SCRIBE_URL,
                headers={"xi-api-key": self.api_key},
                files={"file": (audio_path.name, f, "audio/wav")},
                data=data,
                timeout=1800,
            )

        if resp.status_code != 200:
            raise RuntimeError(f"ElevenLabs returned {resp.status_code}: {resp.text[:500]}")

        return resp.json()
