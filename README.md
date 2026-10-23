# Igris — Voice Assistant

A Windows laptop voice assistant with a React web interface and optional F9
keyboard-driven microphone input.

## Quick start

1. Open a terminal in this folder.
2. Create a `.env` file in this folder and choose an AI provider. For Gemini:
   ```powershell
   GEMINI_API_KEY=your_api_key_here
   AI_PROVIDER=gemini
   ```
   To use Claude instead, set:
   ```text
   AI_PROVIDER=claude
   ANTHROPIC_API_KEY=your_anthropic_api_key
   ```
   You can optionally set `CLAUDE_MODEL` to choose a different Claude model.
   To choose the Jarvis voice, add a Windows TTS voice name such as:
   ```text
   JARVIS_VOICE="Microsoft David Desktop - English (United States)"
   ```
   If the configured voice is missing, the assistant falls back to the system default.
3. Start the keyboard-driven assistant directly with uv:
   ```powershell
   uv run main.py
   ```
   Run this command from the project folder whenever you want to start the assistant.
   You do not need to run `Activate.ps1` first: activation only changes the terminal's
   Python environment and does not start the assistant. On first run, uv creates
   `.venv` and installs the dependencies from `pyproject.toml`.
   In VS Code, use the `.venv` interpreter (`Python: Select Interpreter`) so
   its integrated terminal and `uv` use the same project environment. If a
   terminal was already activated with `venv`, close it and open a new one
   after selecting `.venv`.

   Alternatively, run the existing `venv` directly without activating it:
   ```powershell
   .\venv\Scripts\python.exe -m pip install -r requirements.txt
   .\venv\Scripts\python.exe main.py
   ```
4. To test the microphone before starting the assistant:
   ```powershell
   uv run ears.py
   ```

Press F9 to talk to the assistant. You can also say "Hey Jarvis" or "Jarvis" before a command, and the assistant will answer without needing a separate wake-word setup.

## Igris web interface

The web interface uses React, TypeScript, Tailwind CSS, and a shadcn-compatible
`src/components/ui` structure. Install Node.js (LTS) and npm if they are not
already installed.

From the project folder, install dependencies and start the UI:

```powershell
cd frontend
npm install
npm run dev
```

In a second PowerShell terminal at the project folder, start the local API:

```powershell
uv run uvicorn api:app --host 127.0.0.1 --port 8000
```

Open the Vite URL shown in the first terminal (normally
`http://localhost:5173`). The API binds only to the local machine. Typed prompts
and browser speech recognition are sent to the existing assistant command
handlers; the microphone button requires a browser that supports the Web Speech
API. Voice recognition availability varies by browser and may require internet
access. F9 microphone input remains available through `uv run main.py`.

The reusable network component is in
`frontend/src/components/ui/interactive-synapse-network.tsx`; the UI and styles
are in `frontend/src/App.tsx` and `frontend/src/index.css`. If moving the
component into a different shadcn project, keep it under `src/components/ui`
(the default configured alias is `@/components/ui`) so shadcn components and
project imports share the expected location.

Say `open Chrome`, `open YouTube`, `open WhatsApp`, or `open my work` to open the Learning CCBP portal in Chrome. Say `open hacking tools` or `open GitHub hacking tools` to open the JavaScript hacking-tools topic on GitHub. Say `Sneha` to hear a kind message. Other web shortcuts open in your default browser; WhatsApp requires you to sign in to WhatsApp Web. Say `search YouTube for ...` to view results, or `play the song ... on YouTube` to open the top matching video's watch page. The assistant can open WhatsApp Web but does not read or send messages.

## Notes

- The first transcription run may download the Whisper model.
- AI requests time out after 30 seconds so a stalled network request does not leave the assistant waiting indefinitely.
- `.env` is ignored by Git; keep API keys there, not in Python source files.
- Running with `uv run` uses the project-managed `.venv`; PowerShell script activation is not required.
