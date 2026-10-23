import os
import subprocess
import webbrowser
from ctypes import POINTER, cast
from urllib.parse import quote_plus

import psutil
import pyautogui
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

APPS = {
    "chrome": "start chrome",
    "notepad": "start notepad",
    "calculator": "start calc",
    "file explorer": "start explorer",
    "spotify": "start spotify:",
    "settings": "start ms-settings:",
}

WEB_APPS = {
    "youtube": ("https://www.youtube.com/", "YouTube"),
    "whatsapp": ("https://web.whatsapp.com/", "WhatsApp Web"),
    "whatsapp web": ("https://web.whatsapp.com/", "WhatsApp Web"),
    "hacking tools": (
        "https://github.com/topics/hacking-tools?l=javascript",
        "GitHub JavaScript hacking-tools topic",
    ),
    "github hacking tools": (
        "https://github.com/topics/hacking-tools?l=javascript",
        "GitHub JavaScript hacking-tools topic",
    ),
}
MY_WORK_URL = "https://learning.ccbp.in/?utm_source=inbound_homepage_login_cta&_gl=1*ouwk2s*_gcl_au*NzkyMDY1NTM1LjE3OTEz"


def open_app(name: str):
    normalized_name = name.lower().strip()
    if normalized_name == "my work":
        subprocess.Popen(f'start chrome "{MY_WORK_URL}"', shell=True)
        return "Opening your work portal in Chrome"

    web_app = WEB_APPS.get(normalized_name)
    if web_app:
        url, display_name = web_app
        webbrowser.open(url)
        return f"Opening {display_name} in your default browser"

    command = APPS.get(normalized_name)
    if not command:
        return f"I don't know the app {name}"
    subprocess.Popen(command, shell=True)
    return f"Opening {normalized_name}"


def search_web(query: str):
    webbrowser.open(f"https://www.google.com/search?q={quote_plus(query)}")
    return f"Searching for {query}"


def search_youtube(query: str):
    webbrowser.open(f"https://www.youtube.com/results?search_query={quote_plus(query)}")
    return f"Searching YouTube for {query}"


def play_youtube(query: str):
    query = query.strip()
    if not query:
        return "Tell me which song you want to play on YouTube."

    try:
        from yt_dlp import YoutubeDL

        with YoutubeDL({"quiet": True, "no_warnings": True, "extract_flat": True}) as youtube:
            results = youtube.extract_info(f"ytsearch1:{query}", download=False)
    except Exception as exc:
        print("YouTube lookup error:", exc)
        return "I couldn't look up that YouTube video. Check your internet connection and try again."

    video = next(
        (entry for entry in (results or {}).get("entries", []) if entry and entry.get("id")),
        None,
    )
    if video is None:
        return f"I couldn't find a YouTube video for {query}."

    video_url = video.get("webpage_url") or f"https://www.youtube.com/watch?v={video['id']}"
    if not webbrowser.open(video_url):
        return "I found the video, but couldn't open your browser."
    return f"Opening {video.get('title') or query} on YouTube."


def type_text(text: str):
    pyautogui.write(text, interval=0.03)
    return "Typed it"


def set_volume(percent: int):
    try:
        speakers = AudioUtilities.GetSpeakers()
        interface = speakers.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        level = max(0, min(100, percent)) / 100
        volume.SetMasterVolumeLevelScalar(level, None)
        return f"Volume set to {percent} percent"
    except Exception:
        return "Volume control is not available on this system"


def battery_status():
    battery = psutil.sensors_battery()
    if battery is None:
        return "Battery information is unavailable"
    return f"Battery is at {int(battery.percent)} percent"


def screenshot():
    path = os.path.expanduser("~/Pictures/screenshot.png")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    pyautogui.screenshot(path)
    return "Screenshot saved to Pictures"
