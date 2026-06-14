"""Abstract base class for transcription backends."""

from abc import ABC, abstractmethod
from pathlib import Path


class TranscriptionBackend(ABC):
    """Base class for transcription backends.

    All backends must produce output in a normalized format with word-level
    timestamps, speaker diarization, and audio event markers. The format
    matches ElevenLabs Scribe output for compatibility with pack_transcripts.py.

    Output format:
    {
        "words": [
            {
                "type": "word" | "spacing" | "audio_event",
                "text": str,
                "start": float,  # seconds
                "end": float,    # seconds
                "speaker_id": str | None
            },
            ...
        ]
    }
    """

    @abstractmethod
    def transcribe(
        self,
        audio_path: Path,
        language: str | None = None,
        num_speakers: int | None = None,
        verbose: bool = True,
    ) -> dict:
        """Transcribe an audio file.

        Args:
            audio_path: Path to audio file (expected to be 16kHz mono WAV).
            language: ISO language code (e.g., 'en'). None for auto-detect.
            num_speakers: Hint for diarization. None for auto-detect.
            verbose: Whether to print progress.

        Returns:
            Dict with 'words' key containing list of word entries with
            type, text, start, end, speaker_id.

        Raises:
            RuntimeError: If transcription fails.
        """
        pass

    @abstractmethod
    def validate_setup(self) -> tuple[bool, str]:
        """Check if this backend is properly set up.

        Returns:
            (is_valid, error_message) tuple. If is_valid is False,
            error_message explains what's missing.
        """
        pass

    @abstractmethod
    def backend_name(self) -> str:
        """Return user-friendly backend name."""
        pass
