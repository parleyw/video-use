"""Pluggable transcription backends for video-use.

Supports:
- ElevenLabs Scribe (cloud, requires API key)
- Whisper (local, open source)
- Faster-Whisper (local, optimized)

Configure via TRANSCRIBER_BACKEND env var or config file.
"""

from .base import TranscriptionBackend
from .elevenlabs import ElevenLabsBackend
from .whisper_backend import WhisperBackend
from .faster_whisper_backend import FasterWhisperBackend
from .whisper_with_diarization import WhisperWithDiarizationBackend
from .faster_whisper_with_diarization import FasterWhisperWithDiarizationBackend

__all__ = [
    "TranscriptionBackend",
    "ElevenLabsBackend",
    "WhisperBackend",
    "FasterWhisperBackend",
    "WhisperWithDiarizationBackend",
    "FasterWhisperWithDiarizationBackend",
    "get_backend",
]


def get_backend(backend_name: str = None) -> TranscriptionBackend:
    """Get a transcription backend by name.

    Args:
        backend_name: One of:
            - 'elevenlabs': Cloud transcription with speaker diarization
            - 'whisper': Local, free, no diarization
            - 'faster-whisper': Local, 4x faster, no diarization
            - 'whisper-diarization': Local Whisper + speaker diarization
            - 'faster-whisper-diarization': Local Faster-Whisper + speaker diarization
            - 'google': Google Cloud Speech-to-Text (requires API key + credentials)
            - 'assemblyai': AssemblyAI (requires API key)
        If None, reads TRANSCRIBER_BACKEND env var or defaults to 'whisper'.

    Returns:
        Instantiated backend.

    Raises:
        ValueError: If backend is unknown or not available.
    """
    import os

    if backend_name is None:
        backend_name = os.environ.get("TRANSCRIBER_BACKEND", "whisper").lower()

    backend_name = backend_name.lower().strip()

    if backend_name == "elevenlabs":
        return ElevenLabsBackend()
    elif backend_name == "whisper":
        return WhisperBackend()
    elif backend_name in ("faster-whisper", "faster_whisper"):
        return FasterWhisperBackend()
    elif backend_name in ("whisper-diarization", "whisper_diarization"):
        return WhisperWithDiarizationBackend()
    elif backend_name in ("faster-whisper-diarization", "faster_whisper_diarization"):
        return FasterWhisperWithDiarizationBackend()
    elif backend_name == "google":
        from .google_cloud_backend import GoogleCloudBackend
        return GoogleCloudBackend()
    elif backend_name == "assemblyai":
        from .assemblyai_backend import AssemblyAIBackend
        return AssemblyAIBackend()
    else:
        raise ValueError(
            f"Unknown transcription backend: {backend_name}\n"
            f"Available backends:\n"
            f"  - elevenlabs: Cloud with speaker diarization\n"
            f"  - whisper: Local, free\n"
            f"  - faster-whisper: Local, faster\n"
            f"  - whisper-diarization: Local Whisper + speaker diarization\n"
            f"  - faster-whisper-diarization: Local Faster-Whisper + speaker diarization\n"
            f"  - google: Google Cloud Speech-to-Text\n"
            f"  - assemblyai: AssemblyAI"
        )
