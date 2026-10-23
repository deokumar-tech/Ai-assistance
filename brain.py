import os
from pathlib import Path

import anthropic
from google import genai
from google.genai import types

# Model options:
#   "gemini-3-flash-preview"  -> Gemini 3 Flash
#   "gemini-3.8-flash"        -> newest Flash model
#   "gemini-flash-latest"     -> always points to the newest Flash
MODEL_NAME = "gemini-3-flash-preview"
CLAUDE_MODEL = "claude-sonnet-4-5"
AI_REQUEST_TIMEOUT_SECONDS = 30


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


def get_api_key():
    return _get_setting("GEMINI_API_KEY")


TOOL_SPECS = [
    {
        "name": "open_app",
        "description": "Open an application or website on the laptop. Supported names include chrome, notepad, calculator, youtube, and whatsapp.",
        "properties": {
            "name": {
                "type": "STRING",
                "enum": ["chrome", "notepad", "calculator", "settings", "file explorer", "spotify", "youtube", "whatsapp"],
            }
        },
        "required": ["name"],
    },
    {
        "name": "search_web",
        "description": "Search Google for a phrase or question",
        "properties": {"query": {"type": "STRING"}},
        "required": ["query"],
    },
    {
        "name": "search_youtube",
        "description": "Search YouTube for videos matching a query",
        "properties": {"query": {"type": "STRING"}},
        "required": ["query"],
    },
    {
        "name": "play_youtube",
        "description": "Find the top YouTube video for a song or query and open its watch page to play it",
        "properties": {"query": {"type": "STRING"}},
        "required": ["query"],
    },
    {
        "name": "type_text",
        "description": "Type text at the current cursor position",
        "properties": {"text": {"type": "STRING"}},
        "required": ["text"],
    },
    {
        "name": "set_volume",
        "description": "Set the system volume from 0 to 100",
        "properties": {"percent": {"type": "INTEGER"}},
        "required": ["percent"],
    },
    {
        "name": "battery_status",
        "description": "Report the current battery level",
        "properties": {},
        "required": [],
    },
    {
        "name": "screenshot",
        "description": "Take a screenshot and save it to Pictures",
        "properties": {},
        "required": [],
    },
]


def _gemini_tools():
    declarations = []
    for spec in TOOL_SPECS:
        parameters = {"type": "OBJECT", "properties": spec["properties"]}
        if spec["required"]:
            parameters["required"] = spec["required"]
        declarations.append(types.FunctionDeclaration(
            name=spec["name"],
            description=spec["description"],
            parameters=parameters,
        ))
    return [types.Tool(function_declarations=declarations)]


def _claude_tools():
    tools = []
    for spec in TOOL_SPECS:
        properties = {
            name: {**prop, "type": prop["type"].lower()}
            for name, prop in spec["properties"].items()
        }
        input_schema = {"type": "object", "properties": properties}
        if spec["required"]:
            input_schema["required"] = spec["required"]
        tools.append({
            "name": spec["name"],
            "description": spec["description"],
            "input_schema": input_schema,
        })
    return tools


TOOLS = _gemini_tools()
CLAUDE_TOOLS = _claude_tools()

SYSTEM_PROMPT = (
    "You control a Windows laptop by voice. Choose the best available tool "
    "for the request. Use play_youtube when asked to play a song or video, and "
    "search_youtube when asked only to search. If no tool fits, "
    "reply briefly in plain text."
)


def _decide_with_gemini(user_text: str):
    api_key = get_api_key()
    if not api_key:
        return None, "Set the GEMINI_API_KEY in your .env file before using the AI brain."

    try:
        client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(
                timeout=AI_REQUEST_TIMEOUT_SECONDS * 1000
            ),
        )
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=user_text,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                tools=TOOLS,
                automatic_function_calling=types.AutomaticFunctionCallingConfig(
                    disable=True
                ),
                max_output_tokens=500,
            ),
        )
    except Exception as exc:
        print("Gemini error:", exc)  # shows the real reason in your terminal
        return None, "The Gemini request failed. Check your API key and internet connection."

    if response.function_calls:
        call = response.function_calls[0]
        return call.name, dict(call.args or {})

    return None, response.text or "I couldn't understand that request."


def _decide_with_claude(user_text: str):
    api_key = _get_setting("ANTHROPIC_API_KEY")
    if not api_key:
        return None, "Set ANTHROPIC_API_KEY in your .env file to use Claude."

    model = _get_setting("CLAUDE_MODEL", CLAUDE_MODEL)
    try:
        client = anthropic.Anthropic(
            api_key=api_key,
            timeout=AI_REQUEST_TIMEOUT_SECONDS,
            max_retries=0,
        )
        response = client.messages.create(
            model=model,
            max_tokens=500,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_text}],
            tools=CLAUDE_TOOLS,
        )
    except Exception as exc:
        print("Claude error:", exc)
        return None, "The Claude request failed. Check your API key and internet connection."

    for block in response.content:
        if block.type == "tool_use":
            return block.name, dict(block.input or {})

    for block in response.content:
        if block.type == "text" and block.text:
            return None, block.text
    return None, "I couldn't understand that request."


def decide(user_text: str):
    provider = (_get_setting("AI_PROVIDER", "gemini") or "gemini").lower()
    if provider == "claude":
        return _decide_with_claude(user_text)
    if provider == "gemini":
        return _decide_with_gemini(user_text)
    return None, "AI_PROVIDER must be set to either 'gemini' or 'claude'."