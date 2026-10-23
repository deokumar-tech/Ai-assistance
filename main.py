import re

import keyboard

import hands
from brain import decide
from ears import record, transcribe
from voice import speak


def normalize_wake_word(text: str) -> str:
    """Strip common wake phrases like 'Hey Jarvis' so the real command still works."""
    cleaned = re.sub(r"^(?:hey|hello)\s+jarvis\b[\s,;:.!?-]*", "", text, flags=re.IGNORECASE)
    cleaned = re.sub(r"^jarvis\b[\s,;:.!?-]*", "", cleaned, flags=re.IGNORECASE)
    return cleaned.strip().strip(" \t\r\n,;:.!?-\"")


def is_wake_phrase(text: str) -> bool:
    normalized = normalize_wake_word(text).lower().strip(" \t\r\n,;:.!?-\"")
    return normalized in {"", "listen", "listening", "wake up", "hey jarvis", "hello jarvis", "jarvis"}


def handle_local_command(text: str):
    lower = text.lower().strip(" \t\r\n,;:.!?-\"")

    if not lower:
        return None

    if re.search(r"\bsneha\b", lower):
        return "Sneha, you are a wonderful, kind, and lovely person. My boss is missing you."

    if lower in {"help", "what can you do", "what can you do for me", "hey jarvis", "hello jarvis", "jarvis"}:
        return "You can open Chrome, YouTube, WhatsApp, or the GitHub JavaScript hacking-tools topic, search Google or YouTube, check battery status, set volume, or take a screenshot."

    if lower in {"listen", "listening", "wake up"}:
        return "Yes, I'm here. How can I help?"

    if lower.startswith("open "):
        app_name = lower.replace("open ", "", 1).strip()
        app_aliases = {
            "chrome": "chrome",
            "notepad": "notepad",
            "calculator": "calculator",
            "settings": "settings",
            "file explorer": "file explorer",
            "spotify": "spotify",
            "youtube": "youtube",
            "you tube": "youtube",
            "whatsapp": "whatsapp",
            "whatsapp web": "whatsapp web",
            "my work": "my work",
            "hacking tools": "hacking tools",
            "github hacking tools": "github hacking tools",
        }
        if app_name in app_aliases:
            return hands.open_app(app_aliases[app_name])

    play_match = re.search(
        r"\bplay\s+(?:(?:the\s+)?(?:song|video|music)\s+)?(.+?)(?:\s+on\s+youtube)?[.!?]*$",
        text,
        re.IGNORECASE,
    )
    if play_match and any(word in lower for word in ("youtube", "song", "video", "music")):
        query = play_match.group(1).strip()
        if query:
            return hands.play_youtube(query)

    youtube_marker = "search youtube for "
    if youtube_marker in lower:
        query = text[lower.index(youtube_marker) + len(youtube_marker):].strip()
        if query:
            return hands.search_youtube(query)

    if "search for " in lower:
        query = text.split("search for ", 1)[1].strip()
        if query:
            return hands.search_web(query)

    if "battery" in lower:
        return hands.battery_status()

    if "take a screenshot" in lower or lower == "screenshot":
        return hands.screenshot()

    if "volume" in lower:
        match = re.search(r"\d{1,3}", lower)
        if match:
            return hands.set_volume(int(match.group(0)))
        return "What volume percent do you want?"

    return None


def process_text(text: str) -> str:
    """Process one recognized or typed request and return the assistant response."""
    cleaned = normalize_wake_word(text)
    if is_wake_phrase(text):
        return "Yes, I'm here. How can I help?"

    local_result = handle_local_command(cleaned)
    if local_result is not None:
        return local_result

    tool_name, args = decide(cleaned)
    if not tool_name:
        return args

    try:
        return getattr(hands, tool_name)(**args)
    except TypeError as exc:
        return f"That action failed: {exc}"


def run():
    speak("Assistant ready. Press F9 to talk.")

    while True:
        keyboard.wait("f9")

        try:
            audio = record(5)
        except Exception as exc:
            speak(f"Microphone error: {exc}")
            continue

        text = transcribe(audio)
        if not text:
            speak("I didn't hear anything.")
            continue

        print(f"You: {text}")
        command = normalize_wake_word(text)

        if "stop assistant" in command.lower():
            speak("Goodbye.")
            break

        response = process_text(command or text)
        speak(response if response is not None else "I didn't catch that. Can you repeat?")


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        print("Shutting down assistant.")
