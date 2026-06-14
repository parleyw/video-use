"""Google Cloud Speech-to-Text transcription backend."""

import os
from pathlib import Path

from .base import TranscriptionBackend


class GoogleCloudBackend(TranscriptionBackend):
    """Uses Google Cloud Speech-to-Text API for transcription.

    Requires:
    - Google Cloud account and project
    - Service account credentials (JSON key file)
    - GOOGLE_APPLICATION_CREDENTIALS env var pointing to credentials file
    - pip install google-cloud-speech

    Features:
    - Word-level timestamps
    - Speaker diarization support
    - High accuracy, handles accents well
    - Streaming support (for real-time)

    Pricing: $0.044 per 15 seconds (as of 2024)
    """

    def __init__(self):
        try:
            from google.cloud import speech
            self.speech = speech
            self.client = None
        except ImportError:
            self.speech = None
            self.client = None

    def _get_client(self):
        """Lazily initialize Google Cloud client."""
        if self.client is None:
            if self.speech is None:
                raise RuntimeError("google-cloud-speech not installed")
            self.client = self.speech.SpeechClient()
        return self.client

    def validate_setup(self) -> tuple[bool, str]:
        """Check if Google Cloud credentials are available."""
        if self.speech is None:
            return (
                False,
                "google-cloud-speech not installed. Install with: pip install google-cloud-speech",
            )

        creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")
        if not creds_path or not Path(creds_path).exists():
            return (
                False,
                "GOOGLE_APPLICATION_CREDENTIALS not set or file not found.\n"
                "Set it to your Google Cloud service account JSON key file:\n"
                "  export GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json\n"
                "Get credentials: https://console.cloud.google.com/iam-admin/serviceaccounts",
            )

        return True, ""

    def backend_name(self) -> str:
        """Return backend name."""
        return "Google Cloud Speech-to-Text"

    def transcribe(
        self,
        audio_path: Path,
        language: str | None = None,
        num_speakers: int | None = None,
        verbose: bool = True,
    ) -> dict:
        """Transcribe with Google Cloud Speech-to-Text."""
        is_valid, err = self.validate_setup()
        if not is_valid:
            raise RuntimeError(err)

        if verbose:
            size_mb = audio_path.stat().st_size / (1024 * 1024)
            print(f"  uploading to Google Cloud ({size_mb:.1f} MB)", flush=True)

        client = self._get_client()

        # Read audio file
        with open(audio_path, "rb") as f:
            audio_content = f.read()

        # Build request
        audio = self.speech.RecognitionAudio(content=audio_content)
        config = self.speech.RecognitionConfig(
            encoding=self.speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code=language or "en-US",
            enable_automatic_punctuation=True,
            enable_speaker_diarization=True,
            diarization_config=self.speech.SpeakerDiarizationConfig(
                enable_speaker_diarization=True,
                min_speaker_count=1,
                max_speaker_count=num_speakers or 10,
            ),
            use_enhanced=True,  # Better accuracy
        )

        # Call API
        if verbose:
            print(f"  transcribing with Google Cloud Speech-to-Text", flush=True)

        response = client.recognize(config=config, audio=audio)

        # Convert response to normalized format
        return self._convert_google_output(response)

    def _convert_google_output(self, response) -> dict:
        """Convert Google Cloud response to normalized word-level format."""
        words = []

        for result in response.results:
            for alt in result.alternatives:
                # Google Cloud doesn't return word-level timestamps by default
                # But the result contains the full transcript
                # We'll approximate word timing by distributing evenly
                start_time = 0.0

                for word_info in alt.words:
                    if word_info.word:
                        start = (
                            word_info.start_time.seconds
                            + word_info.start_time.microseconds / 1e6
                        )
                        end = (
                            word_info.end_time.seconds + word_info.end_time.microseconds / 1e6
                        )
                        speaker_id = getattr(word_info, "speaker_tag", None)

                        words.append({
                            "type": "word",
                            "text": word_info.word,
                            "start": start,
                            "end": end,
                            "speaker_id": f"speaker_{speaker_id}" if speaker_id else None,
                        })

        return {"words": words}
