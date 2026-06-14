# Video-use Transcription Backends

Choose any transcription backend you prefer — video-use works with all of them.

## Quick Start

**Local (recommended for most users):**
```bash
pip install faster-whisper
TRANSCRIBER_BACKEND=faster-whisper python helpers/transcribe.py video.mp4
```

**Cloud (fastest, requires API key):**
```bash
pip install requests
export ELEVENLABS_API_KEY=your_key_here
TRANSCRIBER_BACKEND=elevenlabs python helpers/transcribe.py video.mp4
```

---

## Backends Comparison

### Quick Reference Table

| Backend | Speed | Cost | Diarization | Setup | Best For |
|---------|-------|------|-------------|-------|----------|
| **Faster-Whisper** | ~15-30 sec/hr | Free | ❌ | `pip install faster-whisper` | ⭐ Default choice |
| **Whisper** | ~1-2 min/hr | Free | ❌ | `pip install openai-whisper` | Budget/privacy |
| **Faster-Whisper + Diarization** | ~30-60 sec/hr | Free | ✅ | `pip install faster-whisper pyannote.audio` | Speaker IDs locally |
| **Whisper + Diarization** | ~2-3 min/hr | Free | ✅ | `pip install openai-whisper pyannote.audio` | Speaker IDs locally |
| **ElevenLabs** | ~5-30 sec/hr | $5-99/mo | ✅ | API key | Speed + accuracy |
| **AssemblyAI** | ~10-30 sec/hr | $0.36/hr | ✅ | API key | Accuracy + speaker IDs |
| **Google Cloud** | ~10-30 sec/hr | $0.044/15s | ✅ | Credentials | Enterprise |

### Detailed Feature Comparison

| Feature | Whisper | Faster-Whisper | ElevenLabs | AssemblyAI | Google Cloud |
|---------|---------|-----------------|------------|------------|--------------|
| **Word-level timestamps** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Speaker diarization** | ❌ (add with pyannote) | ❌ (add with pyannote) | ✅ | ✅ | ✅ |
| **Punctuation** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Language support** | 99 languages | 99 languages | 20+ languages | 100+ languages | 125+ languages |
| **Streaming** | ❌ | ❌ | ❌ | ✅ | ✅ |
| **Entity recognition** | ❌ | ❌ | ❌ | ✅ | ✅ |
| **Content moderation** | ❌ | ❌ | ❌ | ✅ | ✅ |
| **Local processing** | ✅ | ✅ | ❌ | ❌ | ❌ |
| **No internet needed** | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Free tier** | ✅ | ✅ | ✅ (10k chars/mo) | ✅ ($50 credits) | ❌ |

## Detailed Guide

### Whisper (Local, OpenAI)

100% open source, runs entirely on your machine. No API key needed.

```bash
# Install
pip install openai-whisper

# Use
TRANSCRIBER_BACKEND=whisper python helpers/transcribe.py video.mp4

# Or set default in .env
echo "TRANSCRIBER_BACKEND=whisper" >> .env
```

**Pros:**
- Free
- Open source
- No API key
- Same accuracy as all Whisper variants

**Cons:**
- Slower (~1-2 min per hour of video on CPU)
- Requires more RAM for larger models
- No speaker diarization

**Model sizes:** tiny, base, small, medium, large. Code uses `base` (140M params).

---

### Faster-Whisper (Local, Optimized)

Optimized rewrite of Whisper using OpenVINO. ~4x faster than Whisper, same accuracy.

```bash
# Install
pip install faster-whisper

# Use
TRANSCRIBER_BACKEND=faster-whisper python helpers/transcribe.py video.mp4
```

**Pros:**
- Free
- Open source
- ~4x faster than Whisper
- Runs on CPU or GPU
- No API key

**Cons:**
- No speaker diarization

**Recommended:** This is the best choice for most local workflows.

---

### ElevenLabs Scribe (Cloud)

Cloud-based transcription with word-level timestamps and speaker diarization built-in.

```bash
# Install
pip install requests

# Set API key
export ELEVENLABS_API_KEY=xi_xxxxxxxxxxxxxxx
# Or add to .env
echo "ELEVENLABS_API_KEY=xi_xxxxxxxxxxxxxxx" >> .env

# Use
TRANSCRIBER_BACKEND=elevenlabs python helpers/transcribe.py video.mp4
```

**Pros:**
- Fastest (~5-30 seconds per hour)
- Built-in speaker diarization
- Word-level timestamps included
- Handles accents better

**Cons:**
- Requires paid API key ($5-99/month)
- Requires internet connection
- Data sent to cloud

**Pricing:** https://elevenlabs.io/pricing
- Free: 10,000 characters/month (~1,600 words)
- Starter: $5/month, 50,000 characters
- Pro: $99/month, 500,000 characters

**Get API key:**
1. Sign up at https://elevenlabs.io
2. Go to API Keys section
3. Copy your key
4. Set as `ELEVENLABS_API_KEY` in .env or environment

---

## Configuration

### Via Environment Variable

```bash
export TRANSCRIBER_BACKEND=faster-whisper
python helpers/transcribe.py video.mp4
```

### Via .env File

```bash
# .env
TRANSCRIBER_BACKEND=faster-whisper
ELEVENLABS_API_KEY=xi_xxxxxxx
```

### Via Command-Line Argument

```bash
python helpers/transcribe.py video.mp4 --backend faster-whisper
```

Priority (highest to lowest):
1. `--backend` argument
2. `TRANSCRIBER_BACKEND` env var
3. Default: `whisper`

---

## Output Format

All backends produce the same output format for compatibility with `pack_transcripts.py`:

```json
{
  "words": [
    {
      "type": "word",
      "text": "hello",
      "start": 0.52,
      "end": 0.68,
      "speaker_id": null
    },
    ...
  ]
}
```

Fields:
- **type**: `"word"`, `"spacing"`, or `"audio_event"`
- **text**: The word or event
- **start**: Start time in seconds
- **end**: End time in seconds
- **speaker_id**: Speaker identifier (only ElevenLabs), otherwise `null`

---

### Whisper + Speaker Diarization

Combines Whisper transcription with pyannote speaker identification.

```bash
# Install
pip install openai-whisper pyannote.audio

# Use
TRANSCRIBER_BACKEND=whisper-diarization python helpers/transcribe.py video.mp4
```

**Pros:**
- Free
- Open source
- Local processing
- Includes speaker identification

**Cons:**
- Slower than Faster-Whisper (~2-3 min per hour)
- Requires HuggingFace token on first run
- Requires ~6GB RAM for diarization model

**Setup:** Requires HuggingFace token for pyannote model. Accept terms at https://huggingface.co/pyannote/speaker-diarization-3.0

---

### Faster-Whisper + Speaker Diarization

Combines Faster-Whisper transcription with pyannote speaker identification. Recommended for local speaker diarization.

```bash
# Install
pip install faster-whisper pyannote.audio

# Use
TRANSCRIBER_BACKEND=faster-whisper-diarization python helpers/transcribe.py video.mp4
```

**Pros:**
- Free
- ~4x faster than Whisper + diarization
- Open source
- Local processing
- Includes speaker identification

**Cons:**
- Requires ~6GB RAM for diarization model
- Requires HuggingFace token on first run

**Recommended for:** Local workflows where you need speaker identification

---

### AssemblyAI

Cloud-based transcription with excellent accuracy and built-in speaker diarization.

```bash
# Install
pip install assemblyai

# Get API key
# Sign up: https://www.assemblyai.com
# Free tier: $50 credits

# Use
export ASSEMBLYAI_API_KEY=your_key_here
TRANSCRIBER_BACKEND=assemblyai python helpers/transcribe.py video.mp4
```

**Pros:**
- Excellent accuracy
- Built-in speaker diarization with speaker labels
- Entity recognition
- Content moderation
- $0.36 per hour transcription
- $50 free trial

**Cons:**
- Requires API key (cloud-based)
- Costs money after free credits

**Pricing:** $0.0001 per second (~$0.36 per hour)

**Best for:** High-accuracy transcription with speaker identification

---

### Google Cloud Speech-to-Text

Google's cloud transcription service with enterprise-grade accuracy.

```bash
# Install
pip install google-cloud-speech

# Set up credentials
# 1. Create service account: https://console.cloud.google.com/iam-admin/serviceaccounts
# 2. Create JSON key file
# 3. Set environment variable
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json

# Use
TRANSCRIBER_BACKEND=google python helpers/transcribe.py video.mp4
```

**Pros:**
- Enterprise-grade accuracy
- Excellent for accented speech
- Streaming support
- Multiple language support
- Speaker diarization

**Cons:**
- Requires Google Cloud account and setup
- Costs money: ~$0.044 per 15 seconds
- Requires service account credentials

**Pricing:** $0.044 per 15 seconds (~$10.56 per hour)

**Best for:** Enterprise deployments, high-volume transcription

---

## Troubleshooting

### "whisper not installed"
```bash
pip install openai-whisper
```

### "faster-whisper not installed"
```bash
pip install faster-whisper
```

### "ELEVENLABS_API_KEY not found"
Set your API key in `.env` or environment:
```bash
export ELEVENLABS_API_KEY=xi_xxxxxxx
```

### "ASSEMBLYAI_API_KEY not found"
Set your API key in `.env` or environment:
```bash
export ASSEMBLYAI_API_KEY=your_key_here
```

### "pyannote.audio not installed"
Required for diarization backends:
```bash
pip install pyannote.audio
# Note: Requires HuggingFace token on first run
# Accept terms at: https://huggingface.co/pyannote/speaker-diarization-3.0
```

### "GOOGLE_APPLICATION_CREDENTIALS not found"
Set path to your Google Cloud service account JSON key:
```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
```
Get credentials: https://console.cloud.google.com/iam-admin/serviceaccounts

### Slow transcription with Whisper
- Switch to `faster-whisper` (4x faster)
- Or use ElevenLabs Scribe (cloud)
- Or use a smaller model: edit `helpers/transcribers/whisper_backend.py` line 51 to use `"tiny"` or `"small"`

### GPU acceleration with Faster-Whisper
Faster-Whisper auto-detects GPU. To force GPU:
```python
# In faster_whisper_backend.py, line 56:
self.model = self.WhisperModel("base", device="cuda", compute_type="float16")
```

### Memory issues with large videos
- Use `faster-whisper` instead of `whisper`
- Use a smaller model size
- Process videos in chunks
- Close other applications

---

## Adding Custom Backends

To add a new backend (e.g., Google Speech-to-Text, AssemblyAI):

1. Create `helpers/transcribers/my_backend.py`:

```python
from .base import TranscriptionBackend
from pathlib import Path

class MyBackend(TranscriptionBackend):
    def validate_setup(self) -> tuple[bool, str]:
        # Check if service is configured
        pass

    def backend_name(self) -> str:
        return "My Service"

    def transcribe(self, audio_path: Path, **kwargs) -> dict:
        # Call your API
        # Return normalized format (see above)
        return {"words": [...]}
```

2. Register in `helpers/transcribers/__init__.py`:

```python
from .my_backend import MyBackend

def get_backend(backend_name: str = None) -> TranscriptionBackend:
    if backend_name == "myservice":
        return MyBackend()
    # ... existing backends
```

3. Update `.env.example` and docs.

---

## Performance Tips

**For fast transcription:**
- Use `faster-whisper` or ElevenLabs
- For ElevenLabs, consider larger videos ($0.001-0.01 per minute)
- Close other apps to free RAM

**For best accuracy:**
- ElevenLabs > Whisper/Faster-Whisper (usually)
- All are very accurate for English
- All struggle with heavy accents/noisy audio

**For speaker diarization:**
- Use ElevenLabs (built-in, accurate)
- Whisper/Faster-Whisper don't include this
- Accuracy improves with `--num-speakers` hint if known

---

## Cost Breakdown

**Whisper/Faster-Whisper (Local):**
- $0 (one-time pip install)

**ElevenLabs:**
- Free tier: 10,000 characters/month
- Typical 10-min video: ~3,000-5,000 characters
- So free tier = ~2-3 videos/month, then $5/month for more

**Recommendation:** Use `faster-whisper` for personal projects, ElevenLabs if you need speaker names or fastest speed.
