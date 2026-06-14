"""AssemblyAI transcription backend."""

import os
import time
from pathlib import Path

from .base import TranscriptionBackend


class AssemblyAIBackend(TranscriptionBackend):
    """Uses AssemblyAI API for transcription.

    Requires:
    - AssemblyAI account (https://www.assemblyai.com)
    - ASSEMBLYAI_API_KEY environment variable or .env file
    - pip install assemblyai

    Features:
    - Word-level timestamps
    - Speaker diarization (with speaker names)
    - Entity recognition (names, companies, etc.)
    - Content moderation
    - Multiple language support
    - Excellent accuracy

    Pricing: $0.0001 per second (~$0.36 per hour)
    Free credits: $50 free tier for new accounts
    """

    API_URL = "https://api.assemblyai.com/v2"

    def __init__(self):
        try:
            import assemblyai as aai
            self.aai = aai
            self.api_key = self._load_api_key()
        except ImportError:
            self.aai = None
            self.api_key = None

    def _load_api_key(self) -> str:
        """Load API key from .env or environment."""
        for candidate in [Path(".env"), Path(__file__).resolve().parent.parent.parent / ".env"]:
            if candidate.exists():
                for line in candidate.read_text().splitlines():
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    if k.strip() == "ASSEMBLYAI_API_KEY":
                        return v.strip().strip('"').strip("'")
        return os.environ.get("ASSEMBLYAI_API_KEY", "")

    def validate_setup(self) -> tuple[bool, str]:
        """Check if AssemblyAI is available and configured."""
        if self.aai is None:
            return (
                False,
                "assemblyai not installed. Install with: pip install assemblyai",
            )
        if not self.api_key:
            return (
                False,
                "ASSEMBLYAI_API_KEY not found in .env or environment.\n"
                "Set it: export ASSEMBLYAI_API_KEY=your_key_here\n"
                "Get key: https://www.assemblyai.com (free $50 credits)",
            )
        return True, ""

    def backend_name(self) -> str:
        """Return backend name."""
        return "AssemblyAI"

    def transcribe(
        self,
        audio_path: Path,
        language: str | None = None,
        num_speakers: int | None = None,
        verbose: bool = True,
    ) -> dict:
        """Transcribe with AssemblyAI."""
        is_valid, err = self.validate_setup()
        if not is_valid:
            raise RuntimeError(err)

        if verbose:
            size_mb = audio_path.stat().st_size / (1024 * 1024)
            print(f"  uploading to AssemblyAI ({size_mb:.1f} MB)", flush=True)

        # Set API key
        self.aai.settings.api_key = self.api_key

        # Configure transcriber
        config = self.aai.TranscriptionConfig(
            language_code=language or "en",
            speaker_labels=True,  # Enable speaker diarization
            speakers_expected=num_speakers,
            punctuate=True,
            format_text=True,
        )

        # Create transcriber
        transcriber = self.aai.Transcriber(config=config)

        # Transcribe
        if verbose:
            print(f"  transcribing with AssemblyAI (this may take a minute...)", flush=True)

        try:
            transcript = transcriber.transcribe(str(audio_path))
        except Exception as e:
            raise RuntimeError(f"AssemblyAI transcription failed: {e}")

        if transcript.status == "error":
            raise RuntimeError(f"AssemblyAI error: {transcript.error}")

        # Convert response to normalized format
        return self._convert_assemblyai_output(transcript)

    def _convert_assemblyai_output(self, transcript) -> dict:
        """Convert AssemblyAI response to normalized word-level format."""
        words = []

        # AssemblyAI provides word-level data directly
        if hasattr(transcript, "words") and transcript.words:
            for word_obj in transcript.words:
                speaker_id = None
                if hasattr(word_obj, "speaker") and word_obj.speaker is not None:
                    speaker_id = f"speaker_{word_obj.speaker}"

                words.append({
                    "type": "word",
                    "text": word_obj.text,
                    "start": word_obj.start / 1000.0,  # AssemblyAI returns ms, convert to s
                    "end": word_obj.end / 1000.0,
                    "speaker_id": speaker_id,
                })
        else:
            # Fallback: parse transcript.text if word-level data unavailable
            # This is less ideal but ensures we still get output
            if hasattr(transcript, "text") and transcript.text:
                tokens = transcript.text.split()
                duration = transcript.duration or 0
                time_per_token = duration / len(tokens) if tokens else 0

                for i, token in enumerate(tokens):
                    start = i * time_per_token
                    end = start + time_per_token

                    words.append({
                        "type": "word",
                        "text": token,
                        "start": start,
                        "end": end,
                        "speaker_id": None,
                    })

        return {"words": words}
