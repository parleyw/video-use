# Quick Start Guide — video-use (Open Source)

Choose your path:

## Path A: Just Works (Recommended) — Faster-Whisper

Fast, local, free. No API key needed. Transcribes ~1 hour of video in 15-30 seconds.

```bash
# 1. Install
pip install faster-whisper

# 2. Clone video-use
git clone https://github.com/yourusername/video-use
cd video-use
ln -s "$(pwd)" ~/.claude/skills/video-use
pip install -e .

# 3. Set backend
echo "TRANSCRIBER_BACKEND=faster-whisper" > .env

# 4. Use
cd /path/to/your/videos
claude
# > edit these into a launch video
```

**Done.** Everything runs on your machine. No API keys, no cloud.

---

## Path B: Totally Free (But Slower) — Whisper

Free, local, open source. Transcribes ~1 hour in 1-2 minutes.

```bash
pip install openai-whisper
echo "TRANSCRIBER_BACKEND=whisper" > .env
# Then follow steps 2-4 from Path A
```

---

## Path C: Fastest Cloud Option — ElevenLabs

Fastest transcription. Built-in speaker diarization. Costs $5-99/month, free tier available.

```bash
# 1. Get API key
# Sign up: https://elevenlabs.io
# Copy your API key from the dashboard

# 2. Configure
echo "TRANSCRIBER_BACKEND=elevenlabs" > .env
echo "ELEVENLABS_API_KEY=xi_YOUR_KEY_HERE" >> .env

# 3. Then follow steps 2 and 4 from Path A
```

---

## Common Tasks

### Switch backends mid-project

```bash
# Option 1: Edit .env
TRANSCRIBER_BACKEND=whisper

# Option 2: Command line
python helpers/transcribe.py video.mp4 --backend faster-whisper

# Option 3: Environment variable
export TRANSCRIBER_BACKEND=faster-whisper
python helpers/transcribe.py video.mp4
```

### Transcribe multiple videos in parallel

```bash
python helpers/transcribe_batch.py /path/to/videos --workers 4
```

All videos transcribe in parallel, cached (skips already-transcribed).

### Check which backend is active

```bash
python helpers/transcribe.py video.mp4 -h
# Shows default backend and options
```

### Troubleshooting

**"whisper not installed"**
```bash
pip install openai-whisper
```

**"faster-whisper not installed"**
```bash
pip install faster-whisper
```

**"ELEVENLABS_API_KEY not found"**
```bash
# Add to .env
ELEVENLABS_API_KEY=xi_your_key_here
```

**Transcription is slow**
- Switch to `faster-whisper` (4x faster than Whisper)
- Or use ElevenLabs for cloud transcription

**Running out of RAM**
- Use smaller Whisper model (edit `helpers/transcribers/whisper_backend.py`)
- Or use `faster-whisper` (more efficient)
- Or use ElevenLabs (cloud-based)

---

## Detailed Comparison

See `helpers/transcribers/README.md` for:
- Detailed speed/cost/accuracy comparison
- Installation instructions for each backend
- Performance tips
- GPU acceleration setup

---

## For Developers

Want to add a new backend (Google Cloud Speech, AssemblyAI, etc.)?

See `CONTRIBUTING.md` for step-by-step instructions.

---

## What Works

- ✅ All video editing features
- ✅ Any backend (Whisper, Faster-Whisper, ElevenLabs)
- ✅ Parallel batch transcription
- ✅ Custom animation overlays
- ✅ Color grading
- ✅ Subtitle burning
- ✅ Session persistence

---

**Have questions?** Check `ARCHITECTURE.md` or open an issue.

**Want to contribute?** See `CONTRIBUTING.md`.
