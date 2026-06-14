"""OpenAI Whisper transcription backend (local, open source)."""

from pathlib import Path

from .base import TranscriptionBackend


class WhisperBackend(TranscriptionBackend):
    """Uses OpenAI Whisper for local transcription.

    100% open source, runs on-machine. Slower than Faster-Whisper but
    same accuracy. No API keys required.

    Requires: pip install openai-whisper
    """

    def __init__(self):
        try:
            import whisper
            self.whisper = whisper
        except ImportError:
            self.whisper = None

    def validate_setup(self) -> tuple[bool, str]:
        """Check if whisper is installed."""
        if self.whisper is None:
            return (
                False,
                "whisper not installed. Install with: pip install openai-whisper",
            )
        return True, ""

    def backend_name(self) -> str:
        """Return backend name."""
        return "OpenAI Whisper (local)"

    def transcribe(
        self,
        audio_path: Path,
        language: str | None = None,
        num_speakers: int | None = None,
        verbose: bool = True,
    ) -> dict:
        """Transcribe with Whisper."""
        is_valid, err = self.validate_setup()
        if not is_valid:
            raise RuntimeError(err)

        if verbose:
            size_mb = audio_path.stat().st_size / (1024 * 1024)
            print(f"  transcribing with Whisper ({size_mb:.1f} MB)", flush=True)

        # Load model (defaults to base, can be adjusted)
        # tiny, base, small, medium, large
        model = self.whisper.load_model("base")

        # Transcribe
        result = model.transcribe(
            str(audio_path),
            language=language,
            verbose=False,
        )

        # Convert Whisper format to our normalized format
        return self._convert_whisper_output(result)

    def _convert_whisper_output(self, whisper_result: dict) -> dict:
        """Convert Whisper output to normalized word-level format."""
        words = []

        for segment in whisper_result.get("segments", []):
            start = segment["start"]
            end = segment["end"]
            text = segment["text"].strip()

            if not text:
                continue

            # Whisper doesn't provide word-level timestamps in base model,
            # so we approximate by splitting on whitespace and distributing time
            tokens = text.split()
            if not tokens:
                continue

            # Distribute time evenly across tokens
            time_per_token = (end - start) / len(tokens)

            for i, token in enumerate(tokens):
                word_start = start + (i * time_per_token)
                word_end = word_start + time_per_token

                words.append({
                    "type": "word",
                    "text": token,
                    "start": word_start,
                    "end": word_end,
                    "speaker_id": None,  # Whisper base doesn't do diarization
                })

        return {"words": words}
