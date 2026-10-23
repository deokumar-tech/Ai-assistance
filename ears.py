import os

import numpy as np
import sounddevice as sd
import speech_recognition as sr

try:
    from faster_whisper import WhisperModel
except Exception as exc:  # pragma: no cover - depends on Windows DLL policy
    WhisperModel = None
    WHISPER_IMPORT_ERROR = exc
else:
    WHISPER_IMPORT_ERROR = None

MODEL_NAME = os.getenv("WHISPER_MODEL", "tiny")
SAMPLE_RATE = 16000

model = None


def _load_whisper_model():
    """Instantiate the faster-whisper model on demand to avoid blocking startup."""
    global model
    if model is not None or WhisperModel is None:
        return model

    try:
        model = WhisperModel(MODEL_NAME, device="cpu", compute_type="int8")
    except Exception as exc:  # pragma: no cover - model files or runtime can vary by machine
        print(f"Whisper model loading failed: {exc}")
        model = False
    return model if model is not False else None


def record(seconds: float = 10.0):
    """Record a short clip from the default microphone."""
    devices = sd.query_devices()
    if not devices:
        raise RuntimeError("No audio devices were found on this machine.")

    print("Listening...")
    try:
        audio = sd.rec(
            int(seconds * SAMPLE_RATE),
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="float32",
        )
        sd.wait()
    except Exception as exc:
        raise RuntimeError(f"Unable to record audio: {exc}") from exc
    return audio.astype(np.float32).flatten()


def transcribe(audio):
    """Transcribe recorded audio to text using the best available recognizer."""
    if audio is None or len(audio) == 0:
        return ""

    whisper_model = _load_whisper_model()
    if whisper_model is not None:
        try:
            segments, _ = whisper_model.transcribe(audio, language="en", vad_filter=True)
            return " ".join(segment.text for segment in segments).strip()
        except Exception as exc:  # pragma: no cover - runtime transcription failures are environment specific
            print(f"Whisper transcription failed: {exc}")

    pcm = np.int16(np.clip(audio, -1.0, 1.0) * 32767)
    audio_data = sr.AudioData(pcm.tobytes(), SAMPLE_RATE, 2)
    recognizer = sr.Recognizer()
    try:
        return recognizer.recognize_google(audio_data).strip()
    except sr.UnknownValueError:
        return ""
    except sr.RequestError:
        return "Speech recognition is unavailable right now."


if __name__ == "__main__":
    try:
        text = transcribe(record())
        print(f"You said: {text or '<no speech detected>'}")
    except Exception as exc:
        if WHISPER_IMPORT_ERROR is not None:
            print(f"Whisper dependency error: {WHISPER_IMPORT_ERROR}")
        print(f"Microphone error: {exc}")
