# Contributing to video-use

## Philosophy

Video-use is designed to be **production-correct** but **artistically flexible**. We welcome contributions that:

- Add new transcription backends (without removing existing ones)
- Improve accuracy/speed of existing features
- Expand animation and grading capabilities
- Enhance the Claude Code interaction loop
- Fix bugs
- Improve documentation

We do NOT accept:

- Changes that lock users into a single backend or service
- Removal of open-source/local options in favor of cloud-only
- Features that require proprietary/expensive APIs without open alternatives

## Adding a New Transcription Backend

### Step 1: Create the Backend Class

Create `helpers/transcribers/myservice.py`:

```python
from .base import TranscriptionBackend
from pathlib import Path

class MyServiceBackend(TranscriptionBackend):
    """Brief description of your backend."""

    def __init__(self):
        # Initialize your client, load configs, etc.
        pass

    def validate_setup(self) -> tuple[bool, str]:
        """Check if backend is properly configured.

        Returns:
            (is_valid, error_msg) tuple.
        """
        # Check for API key, installed libraries, network connectivity, etc.
        if not self.api_key:
            return False, "API_KEY not found. Set MY_SERVICE_API_KEY env var or add to .env"
        return True, ""

    def backend_name(self) -> str:
        """Return user-friendly name for logging."""
        return "My Service"

    def transcribe(
        self,
        audio_path: Path,
        language: str | None = None,
        num_speakers: int | None = None,
        verbose: bool = True,
    ) -> dict:
        """Transcribe audio file.

        Args:
            audio_path: Path to 16kHz mono WAV file.
            language: Optional ISO language code.
            num_speakers: Optional hint for diarization.
            verbose: Print progress.

        Returns:
            Dict with 'words' key containing list of normalized word entries.
            Each entry must have: type, text, start, end, speaker_id.

        Raises:
            RuntimeError: If transcription fails.
        """
        is_valid, err = self.validate_setup()
        if not is_valid:
            raise RuntimeError(err)

        if verbose:
            print(f"  transcribing with {self.backend_name()}")

        # Call your API
        result = self._call_api(audio_path, language, num_speakers)

        # Convert to normalized format
        return self._normalize_output(result)

    def _call_api(self, audio_path: Path, language: str | None, num_speakers: int | None) -> dict:
        """Call your transcription service. Return raw response."""
        # Implement API calls here
        pass

    def _normalize_output(self, raw_result: dict) -> dict:
        """Convert your API's output format to normalized word-level format.

        Expected output format:
        {
            "words": [
                {
                    "type": "word",           # "word", "spacing", "audio_event"
                    "text": "hello",
                    "start": 0.52,            # seconds
                    "end": 0.68,              # seconds
                    "speaker_id": None        # or speaker identifier if available
                },
                ...
            ]
        }
        """
        words = []
        # Parse raw_result and convert to word entries
        # ...
        return {"words": words}
```

### Step 2: Register the Backend

Edit `helpers/transcribers/__init__.py`:

```python
from .myservice import MyServiceBackend

def get_backend(backend_name: str = None) -> TranscriptionBackend:
    # ... existing code ...

    elif backend_name in ("myservice", "my-service"):
        return MyServiceBackend()

    else:
        raise ValueError(...)
```

### Step 3: Add Dependencies

Edit `pyproject.toml`:

```toml
[project.optional-dependencies]
transcribers-myservice = ["requests", "my-service-sdk"]  # add your deps
```

### Step 4: Document It

Add a section to `helpers/transcribers/README.md`:

```markdown
### My Service

Brief description of the service.

```bash
# Install
pip install requests my-service-sdk

# Use
export MY_SERVICE_API_KEY=your_key_here
TRANSCRIBER_BACKEND=myservice python helpers/transcribe.py video.mp4
```

**Pros:**
- Advantage 1
- Advantage 2

**Cons:**
- Disadvantage 1

**Pricing:** [link to pricing page]
**Speed:** ~X seconds per hour of video
**Accuracy:** [comparison to other backends]
```

### Step 5: Update Configuration

Edit `.env.example`:

```bash
# Only needed if TRANSCRIBER_BACKEND=myservice
MY_SERVICE_API_KEY=
```

### Step 6: Test

```bash
# Create a test video or use an existing one
export TRANSCRIBER_BACKEND=myservice
export MY_SERVICE_API_KEY=test_key_here
python helpers/transcribe.py test_video.mp4

# Check the output
cat edit/transcripts/test_video.json | jq '.words | length'

# Verify format
python helpers/pack_transcripts.py --edit-dir edit/

# Run a full editing session
cd /path/to/test/videos
claude
# > edit these into a video
```

### Step 7: Open a PR

Include:
- Your backend implementation
- Updated documentation
- Test results (video, transcript output, full editing session)
- Pros/cons compared to other backends

## Adding Other Features

### New Grading Filters

Edit `helpers/grade.py` to add presets or improve the filter chain.

### New Animation Types

Create new animation scripts in `animations/` or extend existing ones.

### Improving the LLM Interaction

Edit `SKILL.md` to document new editing capabilities or improve the prompt structure.

### Bug Fixes

Submit a PR with:
- Description of the bug
- Minimal reproducible example
- Your fix
- Tests if applicable

## Code Style

- Follow PEP 8
- Add docstrings to public functions/classes
- Use type hints (Python 3.10+)
- Avoid unnecessary dependencies
- Test your changes before submitting

## Documentation

- Update `SKILL.md` if you change editing behavior
- Update `ARCHITECTURE.md` if you change the system design
- Update `README.md` for user-facing changes
- Add comments for non-obvious code

## Testing Checklist

Before submitting:

- [ ] Backend validates its setup correctly
- [ ] Transcription produces normalized output
- [ ] Output works with `pack_transcripts.py`
- [ ] Full video editing session completes
- [ ] Documentation is clear and complete
- [ ] No breaking changes to existing backends

## Questions?

Open an issue or discussion thread. We're happy to help.

## License

By contributing, you agree that your contributions are licensed under the same license as this project.
