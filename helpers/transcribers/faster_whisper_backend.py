"""Faster-Whisper transcription backend (optimized local, open source)."""

from pathlib import Path

from .base import TranscriptionBackend


class FasterWhisperBackend(TranscriptionBackend):
    """Uses Faster-Whisper for optimized local transcription.

    ~4x faster than Whisper with same accuracy. Runs on CPU or GPU.
    No API keys required.

    Requires: pip install faster-whisper
    """

    def __init__(self):
        try:
            from faster_whisper import WhisperModel
            self.WhisperModel = WhisperModel
        except ImportError:
            self.WhisperModel = None
        self.model = None

    def validate_setup(self) -> tuple[bool, str]:
        """Check if faster-whisper is installed."""
        if self.WhisperModel is None:
            return (
                False,
                "faster-whisper not installed. Install with: pip install faster-whisper",
            )
        return True, ""

    def backend_name(self) -> str:
        """Return backend name."""
        return "Faster-Whisper (local, optimized)"

    def transcribe(
        self,
        audio_path: Path,
        language: str | None = None,
        num_speakers: int | None = None,
        verbose: bool = True,
    ) -> dict:
        """Transcribe with Faster-Whisper."""
        is_valid, err = self.validate_setup()
        if not is_valid:
            raise RuntimeError(err)

        if verbose:
            size_mb = audio_path.stat().st_size / (1024 * 1024)
            print(f"  transcribing with Faster-Whisper ({size_mb:.1f} MB)", flush=True)

        # Load model once
        if self.model is None:
            self.model = self.WhisperModel("base", device="auto", compute_type="auto")

        # Transcribe
        segments, info = self.model.transcribe(
            str(audio_path),
            language=language,
            beam_size=5,
        )

        # Convert to list to iterate multiple times if needed
        segments = list(segments)

        # Convert Faster-Whisper format to our normalized format
        return self._convert_whisper_output(segments)

    def _convert_whisper_output(self, segments) -> dict:
        """Convert Faster-Whisper output to normalized word-level format."""
        words = []

        for segment in segments:
            start = segment.start
            end = segment.end
            text = segment.text.strip()

            if not text:
                continue

            # Faster-Whisper doesn't provide word-level timestamps by default,
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
                    "speaker_id": None,  # Faster-Whisper doesn't do diarization in base
                })

        return {"words": words}
