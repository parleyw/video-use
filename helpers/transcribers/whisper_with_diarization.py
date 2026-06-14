"""Whisper with speaker diarization via pyannote.

Combines OpenAI Whisper for transcription with pyannote-audio for speaker
diarization, enabling speaker labeling for local transcription.
"""

from pathlib import Path

from .whisper_backend import WhisperBackend


class WhisperWithDiarizationBackend(WhisperBackend):
    """Whisper + pyannote speaker diarization.

    Requires: pip install openai-whisper pyannote.audio

    Slower than plain Whisper (adds diarization time) but enables
    speaker identification in the normalized output.
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
        """Check if whisper and pyannote are installed."""
        if self.whisper is None:
            return False, "whisper not installed. Install with: pip install openai-whisper"
        if self.Pipeline is None:
            return (
                False,
                "pyannote.audio not installed. Install with: pip install pyannote.audio\n"
                "Note: Requires HuggingFace token. See: https://huggingface.co/pyannote/speaker-diarization",
            )
        return True, ""

    def backend_name(self) -> str:
        """Return backend name."""
        return "Whisper + pyannote Diarization (local)"

    def transcribe(
        self,
        audio_path: Path,
        language: str | None = None,
        num_speakers: int | None = None,
        verbose: bool = True,
    ) -> dict:
        """Transcribe with Whisper and add speaker diarization."""
        is_valid, err = self.validate_setup()
        if not is_valid:
            raise RuntimeError(err)

        if verbose:
            size_mb = audio_path.stat().st_size / (1024 * 1024)
            print(f"  transcribing with Whisper + pyannote ({size_mb:.1f} MB)", flush=True)

        # Load Whisper model
        if self.whisper_model is None:
            self.whisper_model = self.whisper.load_model("base")

        # Transcribe
        result = self.whisper_model.transcribe(
            str(audio_path),
            language=language,
            verbose=False,
        )

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

        # Convert Whisper output to normalized format with speaker info
        return self._convert_whisper_with_diarization(result, diarization)

    def _convert_whisper_with_diarization(self, whisper_result: dict, diarization) -> dict:
        """Convert Whisper output + diarization to normalized word-level format."""
        words = []

        for segment in whisper_result.get("segments", []):
            start = segment["start"]
            end = segment["end"]
            text = segment["text"].strip()

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

    @property
    def whisper_model(self):
        """Lazy-load Whisper model."""
        if not hasattr(self, "_whisper_model"):
            self._whisper_model = None
        return self._whisper_model

    @whisper_model.setter
    def whisper_model(self, value):
        self._whisper_model = value
