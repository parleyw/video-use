# video-use Fork — Open Source with Pluggable Transcription Backends

This is a forked version of video-use with a major architectural improvement: **pluggable transcription backends** that let users choose their own transcription service or run everything locally.

## What Changed

### 1. **Transcription Now Pluggable** (the big one)

Before: Hardcoded to ElevenLabs Scribe API only.

Now: Choose from:
- **Faster-Whisper** (local, ~4x faster than Whisper, free) ← **Recommended**
- **Whisper** (local, open source, free)
- **ElevenLabs** (cloud, fastest, $5-99/mo)
- **Custom:** Easy to add new backends

All backends produce the same output format, so the rest of the pipeline works identically.

### 2. **New Folder Structure**

```
helpers/transcribers/
├── __init__.py              # Backend factory (get_backend())
├── base.py                  # Abstract backend interface
├── whisper_backend.py       # Whisper implementation
├── faster_whisper_backend.py # Faster-Whisper implementation
├── elevenlabs.py            # ElevenLabs implementation
└── README.md                # Detailed backend comparison + setup guide
```

### 3. **Updated Entry Points**

- `helpers/transcribe.py` — Now uses pluggable backends, `--backend` argument
- `helpers/transcribe_batch.py` — Same, with parallel transcription support

### 4. **Configuration**

Set your transcription backend via (in priority order):
1. `--backend` CLI argument: `python helpers/transcribe.py --backend faster-whisper video.mp4`
2. `TRANSCRIBER_BACKEND` env var: `export TRANSCRIBER_BACKEND=faster-whisper`
3. `.env` file: `TRANSCRIBER_BACKEND=faster-whisper`
4. Default: Whisper (local, free, no API key)

### 5. **New Documentation**

- **`ARCHITECTURE.md`** — Design rationale, how backends work, how to add new ones
- **`CONTRIBUTING.md`** — Step-by-step guide for adding new backends
- **`helpers/transcribers/README.md`** — Detailed backend comparison, pricing, speed, setup
- **Updated `SKILL.md`** — Reflects pluggable backends, updated setup instructions
- **Updated `README.md`** — Shows all transcription options, quick start

### 6. **Updated Dependencies**

`pyproject.toml` now has optional transcriber groups:

```toml
[project.optional-dependencies]
transcribers-whisper = ["openai-whisper"]
transcribers-faster = ["faster-whisper"]
transcribers-elevenlabs = ["requests"]  # already in main deps
transcribers-all = ["openai-whisper", "faster-whisper", "requests"]
```

Users install only what they need:
```bash
pip install faster-whisper        # for Faster-Whisper
pip install openai-whisper        # for Whisper
# No extra install for ElevenLabs (requests already required)
```

## Quick Start

### 1. Clone and Install

```bash
git clone https://github.com/yourusername/video-use
cd video-use
ln -s "$(pwd)" ~/.claude/skills/video-use
pip install -e .
```

### 2. Choose Your Backend

**Option A: Faster-Whisper (recommended, local, fastest free option)**
```bash
pip install faster-whisper
export TRANSCRIBER_BACKEND=faster-whisper
```

**Option B: Whisper (local, free, slower)**
```bash
pip install openai-whisper
export TRANSCRIBER_BACKEND=whisper
```

**Option C: ElevenLabs (cloud, fastest, requires API key)**
```bash
export TRANSCRIBER_BACKEND=elevenlabs
export ELEVENLABS_API_KEY=xi_xxxxx
# Or add to .env
```

### 3. Use Normally

```bash
cd /path/to/your/videos
claude
# > edit these into a launch video
```

## Architecture Highlights

### Backend Interface (Simple & Extensible)

All backends implement:

```python
class TranscriptionBackend(ABC):
    def transcribe(self, audio_path, language=None, num_speakers=None) -> dict:
        """Return {"words": [...]"""
        pass

    def validate_setup(self) -> tuple[bool, str]:
        """Check if configured. Return (is_valid, error_msg)"""
        pass

    def backend_name(self) -> str:
        """Return friendly name"""
        pass
```

### Normalized Output Format

All backends produce this format (compatible with `pack_transcripts.py`):

```json
{
  "words": [
    {
      "type": "word",
      "text": "hello",
      "start": 0.52,
      "end": 0.68,
      "speaker_id": null
    }
  ]
}
```

This means the entire pipeline is backend-agnostic — swap transcribers without changing anything else.

## Adding New Backends

It's easy! See `ARCHITECTURE.md` and `CONTRIBUTING.md` for detailed instructions.

Quick version:
1. Create `helpers/transcribers/myservice.py` implementing `TranscriptionBackend`
2. Register in `helpers/transcribers/__init__.py`
3. Add to `.env.example` and `pyproject.toml`
4. Document in `helpers/transcribers/README.md`
5. Open a PR

## Cost Comparison

| Backend | Cost | Speed | Setup |
|---------|------|-------|-------|
| Whisper | Free | ~1-2 min/hr | `pip install openai-whisper` |
| Faster-Whisper | Free | ~15-30 sec/hr | `pip install faster-whisper` |
| ElevenLabs | $0-99/mo | ~5-30 sec/hr | API key + `requests` |

**Recommendation:** Use Faster-Whisper for local workflows (free, fast, private). Use ElevenLabs if you need fastest speed or speaker diarization.

## Backward Compatibility

- Existing `.env` files with `ELEVENLABS_API_KEY` still work
- Default behavior changed: now uses Whisper instead of ElevenLabs
  - To keep using ElevenLabs: set `TRANSCRIBER_BACKEND=elevenlabs`
- All downstream code (`pack_transcripts.py`, `render.py`, etc.) is unchanged
- No changes to editing workflow, SKILL.md rules, or output quality

## What's NOT Changed

- Video editing pipeline (render.py, grade.py, etc.) — fully compatible
- SKILL.md production rules — still apply
- Editing interaction with Claude Code — same as before
- Output quality — all backends produce high-quality transcripts

## Philosophy

This fork prioritizes **user choice** over vendor lock-in:

- No forced cloud dependencies
- Run everything on-machine if you prefer
- No paid API key required for basic use
- Easy to add your favorite transcription service
- Privacy-friendly (local backends send no data to cloud)

## Next Steps

For this to be useful, you'll want to:

1. **Test each backend** with a real video to ensure they work on your system
2. **Add speaker diarization** to local backends (Whisper/Faster-Whisper)
3. **Set up GitHub** to track issues and accept pull requests
4. **Document platform-specific setup** (macOS, Linux, Windows Subsystem for Linux)

## Files Changed

New files:
- `helpers/transcribers/__init__.py`
- `helpers/transcribers/base.py`
- `helpers/transcribers/whisper_backend.py`
- `helpers/transcribers/faster_whisper_backend.py`
- `helpers/transcribers/elevenlabs.py`
- `helpers/transcribers/README.md`
- `ARCHITECTURE.md`
- `CONTRIBUTING.md`
- `FORK_SUMMARY.md` (this file)

Modified files:
- `helpers/transcribe.py` — Now uses pluggable backends
- `helpers/transcribe_batch.py` — Same
- `pyproject.toml` — Added optional transcriber dependencies
- `.env.example` — Documented TRANSCRIBER_BACKEND config
- `README.md` — Added backend selection instructions
- `SKILL.md` — Updated setup + helpers documentation

Unchanged:
- All rendering, grading, animation, subtitle logic
- Editing workflow
- SKILL.md production rules
- Downstream pipeline

---

**Questions or issues?** See `ARCHITECTURE.md` for technical details or `CONTRIBUTING.md` for contribution guidelines.
