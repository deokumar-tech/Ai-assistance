import os
from pathlib import Path

import pyttsx3


def _get_setting(name: str, default: str | None = None):
    value = os.getenv(name)
    if value:
        return value.strip()

    env_path = Path(__file__).resolve().with_name(".env")
    if env_path.exists():
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            key, separator, setting_value = line.partition("=")
            if separator and key.strip() == name:
                return setting_value.strip().strip("\"'") or default
    return default


engine = pyttsx3.init()
engine.setProperty("rate", 175)


def get_available_voices() -> list[str]:
    return [voice.name for voice in engine.getProperty("voices")]


def set_voice(preferred_name: str | None = None) -> str | None:
    voices = engine.getProperty("voices")
    if not voices:
        return None

    requested_name = (preferred_name or _get_setting(
        "JARVIS_VOICE",
        "Microsoft David Desktop - English (United States)",
    ) or voices[0].name).strip()

    requested_name_lower = requested_name.casefold()
    for voice in voices:
        if voice.name.casefold() == requested_name_lower or requested_name_lower in voice.name.casefold():
            engine.setProperty("voice", voice.id)
            return voice.name

    engine.setProperty("voice", voices[0].id)
    return voices[0].name


set_voice()


def speak(text: str):
    try:
        engine.say(text)
        engine.runAndWait()
    except Exception as exc:
        print(f"Assistant: {text}")
        print(f"TTS error: {exc}")
