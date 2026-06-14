"""Faster-Whisper with speaker diarization via pyannote.

Combines Faster-Whisper for transcription with pyannote-audio for speaker
diarization. Faster than regular Whisper + diarization.
"""

from pathlib import Path

from .faster_whisper_backend import FasterWhisperBackend


class FasterWhisperWithDiarizationBackend(FasterWhisperBackend):
    """Faster-Whisper + pyannote speaker diarization.

    Requires: pip install faster-whisper pyannote.audio

    Combines the speed of Faster-Whisper (~15-30 sec/hr) with speaker
    identification via pyannote diarization.
    """

    def __init__(self):
        super().__init__()
        try:
            from pyannote.audio import Pipeline
            self.Pipeline = Pipeline
            self.diarization_pipeline = None
        except ImportError:
            self.Pipeline = None

    def validate_setup(self) -> tuple[bool, str]:
        """Check if faster-whisper and pyannote are installed."""
        if self.WhisperModel is None:
            return False, "faster-whisper not installed. Install with: pip install faster-whisper"
        if self.Pipeline is None:
            return (
                False,
                "pyannote.audio not installed. Install with: pip install pyannote.audio\n"
                "Note: Requires HuggingFace token. See: https://huggingface.co/pyannote/speaker-diarization",
            )
        return True, ""

    def backend_name(self) -> str:
        """Return backend name."""
        return "Faster-Whisper + pyannote Diarization (local, optimized)"

    def transcribe(
        self,
        audio_path: Path,
        language: str | None = None,
        num_speakers: int | None = None,
        verbose: bool = True,
    ) -> dict:
        """Transcribe with Faster-Whisper and add speaker diarization."""
        is_valid, err = self.validate_setup()
        if not is_valid:
            raise RuntimeError(err)

        if verbose:
            size_mb = audio_path.stat().st_size / (1024 * 1024)
            print(f"  transcribing with Faster-Whisper + pyannote ({size_mb:.1f} MB)", flush=True)

        # Load Faster-Whisper model
        if self.model is None:
            self.model = self.WhisperModel("base", device="auto", compute_type="auto")

        # Transcribe
        segments, info = self.model.transcribe(
            str(audio_path),
            language=language,
            beam_size=5,
        )
        segments = list(segments)

        # Load diarization pipeline
        if self.diarization_pipeline is None:
            if verbose:
                print(f"  loading diarization model (first time only)", flush=True)
            self.diarization_pipeline = self.Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.0",
                use_auth_token=True,  # Requires HuggingFace token
            )

        # Get diarization
        if verbose:
            print(f"  running speaker diarization", flush=True)
        diarization = self.diarization_pipeline(str(audio_path), num_speakers=num_speakers)

        # Convert Faster-Whisper output + diarization to normalized format
        return self._convert_whisper_with_diarization(segments, diarization)

    def _convert_whisper_with_diarization(self, segments, diarization) -> dict:
        """Convert Faster-Whisper output + diarization to normalized word-level format."""
        words = []

        for segment in segments:
            start = segment.start
            end = segment.end
            text = segment.text.strip()

            if not text:
                continue

            # Find the speaker at this segment's midpoint
            segment_mid = (start + end) / 2
            speaker_id = None
            for turn, _, speaker in diarization.iterturn():
                if turn.start <= segment_mid <= turn.end:
                    speaker_id = speaker
                    break

            # Split into tokens
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
                    "speaker_id": speaker_id,
                })

        return {"words": words}
