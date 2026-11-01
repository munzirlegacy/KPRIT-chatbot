# KPRIT Chatbot

A lightweight real-time AI chatbot web app for KPRIT, built with FastAPI and powered by Google's Gemini API. The app streams responses in real time from the backend to a sleek browser-based chat UI.

## Features

- Real-time streaming chat responses
- FastAPI backend with SSE streaming
- Browser UI for interactive conversation
- Session-based in-memory chat history
- Gemini API integration with .env-based configuration
- Simple startup script for local development

## Project Structure

```text
KPRIT-chatbot/
├── LICENSE
├── README.md
├── .gitignore
└── AIHAIAI/
    └── chatbot/
        ├── index.html
        ├── main.py
        ├── requirements.txt
        ├── start.ps1
        └── .env.example (optional, if added locally)
```

## Tech Stack

- Python 3.10+
- FastAPI
- Uvicorn
- Google GenAI SDK
- HTML/CSS/JavaScript frontend

## Setup

1. Open a terminal in the `AIHAIAI/chatbot` folder.
2. Create and activate a virtual environment.
3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the same folder and add your Gemini API key:

```env
GEMINI_API_KEY=your_api_key_here
MODEL_NAME=gemini-2.5-flash
```

> If `MODEL_NAME` is omitted, the app uses a default Gemini model value.

## Run the App

### Option 1: PowerShell script

On Windows:

```powershell
cd AIHAIAI/chatbot
./start.ps1
```

### Option 2: Manual run

```bash
cd AIHAIAI/chatbot
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Then open:

```text
http://localhost:8000
```

## How It Works

- The frontend sends user messages to `/chat/stream`.
- The backend stores chat history in memory per session.
- Gemini generates a response stream.
- The UI displays tokens as they arrive for a live chat effect.

## Notes

- Chat history is stored in memory only and resets when the server restarts or the session is cleared.
- The app uses a default in-memory session store and does not persist data to a database.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Author

KPRIT Chatbot
