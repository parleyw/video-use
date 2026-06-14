# Video-use Architecture

## Overview

Video-use is a conversational video editor that uses Claude Code to reason about video content. The key architectural decision is **pluggable transcription backends** — users can choose where their audio gets transcribed (local, on-machine, or cloud-based).

## Pluggable Transcription Backends

The transcription layer is abstracted behind a simple interface in `helpers/transcribers/`:

### Backend Interface

All backends inherit from `TranscriptionBackend` and implement:

```python
class TranscriptionBackend(ABC):
    @abstractmethod
    def transcribe(self, audio_path, language=None, num_speakers=None, verbose=True) -> dict:
        """Transcribe audio. Returns normalized word-level format."""
        pass

    @abstractmethod
    def validate_setup(self) -> tuple[bool, str]:
        """Check if backend is properly configured. Returns (is_valid, error_msg)."""
        pass

    @abstractmethod
    def backend_name(self) -> str:
        """Return user-friendly name."""
        pass
```

### Available Backends

| Backend | File | Speed | Cost | Notes |
|---------|------|-------|------|-------|
| Whisper | `whisper_backend.py` | ~1-2 min/hr | Free | Local, open source, baseline accuracy |
| Faster-Whisper | `faster_whisper_backend.py` | ~15-30 sec/hr | Free | Local, optimized, same accuracy as Whisper |
| ElevenLabs | `elevenlabs.py` | ~5-30 sec/hr | $5-99/mo | Cloud, fastest, includes speaker diarization |

### Using a Backend

Backends are selected via the `get_backend()` factory function in `helpers/transcribers/__init__.py`:

```python
from transcribers import get_backend

backend = get_backend("faster-whisper")  # or "whisper", "elevenlabs"
result = backend.transcribe(audio_path, language="en")
```

Priority order (if no backend specified):
1. Command-line `--backend` argument
2. `TRANSCRIBER_BACKEND` environment variable
3. Default: `"whisper"` (local, free, no API key)

### Normalized Output Format

All backends produce this format for compatibility with `pack_transcripts.py`:

```json
{
  "words": [
    {
      "type": "word",           // "word", "spacing", or "audio_event"
      "text": "hello",
      "start": 0.52,            // seconds
      "end": 0.68,              // seconds
      "speaker_id": null        // only ElevenLabs populates this
    },
    ...
  ]
}
```

This normalization means the rest of the pipeline (`pack_transcripts.py`, rendering, etc.) works identically regardless of which backend is used.

## Adding a New Backend

To add support for a new transcription service (e.g., Google Cloud Speech-to-Text, AssemblyAI):

1. **Create `helpers/transcribers/my_service.py`:**

```python
from .base import TranscriptionBackend
from pathlib import Path

class MyServiceBackend(TranscriptionBackend):
    def validate_setup(self) -> tuple[bool, str]:
        # Check for API key, libraries, connectivity, etc.
        # Return (is_valid, error_message)
        pass

    def backend_name(self) -> str:
        return "My Service"

    def transcribe(self, audio_path: Path, language=None, num_speakers=None, verbose=True) -> dict:
        # Call your API
        # Convert output to normalized format
        return {"words": [...]}
```

2. **Register in `helpers/transcribers/__init__.py`:**

```python
from .my_service import MyServiceBackend

def get_backend(backend_name: str = None) -> TranscriptionBackend:
    # ... existing code ...
    elif backend_name == "myservice":
        return MyServiceBackend()
    # ...
```

3. **Update `.env.example` with configuration:**

```bash
TRANSCRIBER_BACKEND=myservice
MY_SERVICE_API_KEY=your_key_here
```

4. **Add to `pyproject.toml` optional dependencies:**

```toml
[project.optional-dependencies]
transcribers-myservice = ["requests"]  # or whatever deps you need
```

5. **Document in `helpers/transcribers/README.md`:**

Add a section explaining pricing, speed, setup, and pros/cons.

## Data Flow

```
Video File
    ↓
[helpers/transcribe.py]
    ├─ Extract 16kHz mono audio via ffmpeg
    ├─ Call transcriber backend
    └─ Save result to <edit>/transcripts/<name>.json
    ↓
[helpers/pack_transcripts.py]
    ├─ Read all transcripts/<name>.json files
    ├─ Group words into phrases (break on silence/speaker change)
    └─ Output <edit>/takes_packed.md (Claude's primary input)
    ↓
[Claude Code]
    ├─ Read takes_packed.md
    ├─ Propose editing strategy
    ├─ Generate EDL (edit decision list)
    ├─ Request visual drill-downs via timeline_view
    └─ Iterate until user approves
    ↓
[helpers/render.py]
    ├─ Execute EDL
    ├─ Extract segments
    ├─ Apply grades, subtitles, overlays
    └─ Output final.mp4
```

## Design Rationale

### Why Pluggable Backends?

1. **User choice:** Some users have API budgets (ElevenLabs), others prefer local-only processing for privacy
2. **Offline capability:** Whisper/Faster-Whisper work entirely on-machine
3. **Cost optimization:** Whisper is free, Faster-Whisper is free, ElevenLabs has free tier + paid
4. **Extensibility:** Easy to add new services without forking the codebase

### Why Normalized Output?

By standardizing on a single output format, the entire downstream pipeline is backend-agnostic. Swapping transcribers doesn't require changes to `pack_transcripts.py`, `render.py`, etc.

### Why Whisper as Default?

Whisper is:
- Free (no API costs)
- Open source (auditable, privacy-friendly)
- Accurate (competitive with paid services)
- Well-maintained (OpenAI)
- Easy to install (`pip install openai-whisper`)

The default is set in `.env.example` and can be overridden per-session.

## Configuration

Configuration happens at three levels (in priority order):

1. **CLI argument:** `python helpers/transcribe.py --backend faster-whisper video.mp4`
2. **Environment variable:** `export TRANSCRIBER_BACKEND=faster-whisper`
3. **Config file (`.env`):** `TRANSCRIBER_BACKEND=faster-whisper`

This allows:
- Default behavior (uses Whisper)
- User preference (set in `.env` once)
- Per-invocation override (via CLI or env var)

## Dependencies

All backends are optional except for the base `requests` library (used by ElevenLabs):

```toml
[project.optional-dependencies]
transcribers-whisper = ["openai-whisper"]
transcribers-faster = ["faster-whisper"]
transcribers-elevenlabs = ["requests"]  # already in main deps
```

Users install only what they need:
- `pip install faster-whisper` for Faster-Whisper
- `pip install openai-whisper` for Whisper
- Nothing extra for ElevenLabs (requests is already required)

Or install all:
```bash
pip install -e ".[transcribers-all]"
```

## Future Improvements

1. **Speaker diarization for local backends:** Add speaker ID detection to Whisper/Faster-Whisper output
2. **Streaming transcription:** Support real-time transcription for live editing workflows
3. **Multi-language support:** Add language detection and per-segment language specification
4. **Custom backend templates:** Scaffold for users to add their own transcribers
5. **Fallback chains:** Try ElevenLabs first, fall back to Faster-Whisper if it fails or rate-limits

## Testing

To test a new backend:

1. Create a test video or use an existing one
2. Set the backend: `export TRANSCRIBER_BACKEND=myservice`
3. Run transcription: `python helpers/transcribe.py test.mp4`
4. Check output in `edit/transcripts/test.json`
5. Verify it follows the normalized format
6. Run packing: `python helpers/pack_transcripts.py --edit-dir edit/`
7. Verify `takes_packed.md` looks correct
8. Run a full video editing session to ensure downstream compatibility
