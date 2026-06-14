"""Test suite for transcription backends.

Generates synthetic test audio and tests all available transcribers.
Usage:
    python helpers/test_transcribers.py                 # Test all backends
    python helpers/test_transcribers.py --backend whisper  # Test specific backend
"""

import argparse
import json
import sys
import tempfile
from pathlib import Path

import numpy as np


def generate_test_audio(duration: float = 10.0, sample_rate: int = 16000) -> Path:
    """Generate synthetic test audio (sine wave).

    Args:
        duration: Audio duration in seconds.
        sample_rate: Sample rate in Hz.

    Returns:
        Path to generated WAV file.
    """
    print(f"Generating {duration}s test audio at {sample_rate}Hz...")

    try:
        import scipy.io.wavfile as wavfile
    except ImportError:
        print("ERROR: scipy required for test audio generation. Install with: pip install scipy")
        sys.exit(1)

    # Generate sine wave (440 Hz tone)
    t = np.linspace(0, duration, int(sample_rate * duration))
    frequency = 440  # A4 note
    audio = (np.sin(2 * np.pi * frequency * t) * 32767).astype(np.int16)

    # Create temp file
    tmp_path = Path(tempfile.gettempdir()) / "test_audio.wav"
    wavfile.write(str(tmp_path), sample_rate, audio)

    print(f"  ✓ Generated {tmp_path} ({audio.nbytes / 1024 / 1024:.2f} MB)")
    return tmp_path


def test_backend(backend_name: str, audio_path: Path) -> bool:
    """Test a single transcription backend.

    Args:
        backend_name: Name of backend to test.
        audio_path: Path to test audio file.

    Returns:
        True if test passed, False otherwise.
    """
    print(f"\n{'='*60}")
    print(f"Testing: {backend_name}")
    print(f"{'='*60}")

    try:
        from transcribers import get_backend
    except ImportError:
        print("ERROR: Cannot import transcribers. Make sure helpers/ is in PYTHONPATH")
        return False

    try:
        backend = get_backend(backend_name)
    except ValueError as e:
        print(f"✗ Backend not available: {e}")
        return False

    # Check setup
    is_valid, err = backend.validate_setup()
    if not is_valid:
        print(f"✗ Backend setup failed:")
        print(f"  {err}")
        return False

    print(f"✓ Backend setup valid: {backend.backend_name()}")

    # Test transcription
    try:
        print(f"  Transcribing test audio...")
        result = backend.transcribe(audio_path, verbose=True)
    except Exception as e:
        print(f"✗ Transcription failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Validate output
    if not isinstance(result, dict) or "words" not in result:
        print(f"✗ Invalid output format: expected {{'words': [...]}}, got {type(result)}")
        return False

    words = result["words"]
    if not words:
        print(f"✗ No words returned")
        return False

    # Print summary
    print(f"✓ Transcription successful!")
    print(f"  Words: {len(words)}")
    print(f"  Duration: {words[-1]['end']:.1f}s")
    print(f"  Sample words:")
    for word in words[:5]:
        print(f"    [{word['start']:.2f}-{word['end']:.2f}] {word['text']}")

    return True


def main() -> None:
    ap = argparse.ArgumentParser(description="Test transcription backends")
    ap.add_argument(
        "--backend",
        type=str,
        default=None,
        help="Test specific backend. If omitted, tests all available backends.",
    )
    ap.add_argument(
        "--audio",
        type=Path,
        default=None,
        help="Path to test audio file. If omitted, generates synthetic audio.",
    )
    ap.add_argument(
        "--keep-audio",
        action="store_true",
        help="Keep generated audio file after tests.",
    )
    args = ap.parse_args()

    # Generate or use provided audio
    if args.audio:
        audio_path = args.audio.resolve()
        if not audio_path.exists():
            sys.exit(f"Audio file not found: {audio_path}")
    else:
        audio_path = generate_test_audio()

    # List of backends to test
    backends_to_test = [
        "whisper",
        "faster-whisper",
        "whisper-diarization",
        "faster-whisper-diarization",
        "elevenlabs",
        "assemblyai",
        "google",
    ]

    if args.backend:
        backends_to_test = [args.backend]

    # Run tests
    results = {}
    for backend_name in backends_to_test:
        passed = test_backend(backend_name, audio_path)
        results[backend_name] = "PASSED" if passed else "FAILED"

    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    for backend_name, status in results.items():
        symbol = "✓" if status == "PASSED" else "✗"
        print(f"{symbol} {backend_name}: {status}")

    passed_count = sum(1 for v in results.values() if v == "PASSED")
    print(f"\nTotal: {passed_count}/{len(results)} backends working")

    # Cleanup
    if not args.keep_audio and not args.audio:
        audio_path.unlink()
        print(f"\nCleaned up test audio: {audio_path}")

    sys.exit(0 if passed_count == len(results) else 1)


if __name__ == "__main__":
    main()
