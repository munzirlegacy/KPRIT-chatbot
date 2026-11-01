"""
Real-time chatbot backend using FastAPI + Google Gemini native SDK streaming (SSE).
Uses google-genai SDK which supports all API key formats including AQ. keys.
Conversation context is stored in-memory per session -- no persistence.
"""

import os
import json
import uuid
from typing import AsyncGenerator

from dotenv import load_dotenv

# Load .env relative to this file — works regardless of working directory
_ENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(dotenv_path=_ENV_PATH)

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai
from google.genai import types

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(title="KPRIT AI Chatbot", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_gemini_client() -> tuple[genai.Client, str]:
    """Create Gemini client using the API key from .env."""
    load_dotenv(dotenv_path=_ENV_PATH, override=True)
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="GEMINI_API_KEY is not set. Add it to your .env file.",
        )
    model_name = os.environ.get("MODEL_NAME", "gemini-3.8-flash")
    client = genai.Client(api_key=api_key)
    return client, model_name

# ---------------------------------------------------------------------------
# In-memory session store  { session_id: [{"role": ..., "parts": [...]}] }
# ---------------------------------------------------------------------------

sessions: dict[str, list[dict]] = {}

SYSTEM_PROMPT = (
    "You are KPRIT AI, a helpful, knowledgeable, and friendly AI assistant for KPRIT. "
    "Answer clearly, concisely, and accurately. If you don't know something, say so."
)

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    session_id: str
    message: str

class SessionResponse(BaseModel):
    session_id: str

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    html_path = os.path.join(os.path.dirname(__file__), "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.post("/session", response_model=SessionResponse)
async def create_session():
    sid = str(uuid.uuid4())
    sessions[sid] = []  # list of {"role": "user"|"model", "parts": [{"text": "..."}]}
    return {"session_id": sid}


@app.api_route("/session/{session_id}", methods=["DELETE", "POST"])
async def delete_session(session_id: str):
    sessions.pop(session_id, None)
    return {"detail": "Session ended."}


@app.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    if req.session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found. Create one via POST /session.")

    history = sessions[req.session_id]

    # Append user message in Gemini native format
    history.append({"role": "user", "parts": [{"text": req.message}]})

    client, model_name = get_gemini_client()

    # Convert history to Gemini Content objects
    gemini_history = [
        types.Content(
            role=msg["role"],
            parts=[types.Part(text=p["text"]) for p in msg["parts"]]
        )
        for msg in history[:-1]  # all but the latest user message
    ]

    async def token_generator() -> AsyncGenerator[str, None]:
        collected_content = []
        try:
            # Explicitly set thinking_level="low" so Gemini responds immediately
            # without prolonged reasoning delays.
            config_kwargs = {
                "system_instruction": SYSTEM_PROMPT,
                "temperature": 0.7,
                "max_output_tokens": 1024,
            }
            try:
                config_kwargs["thinking_config"] = types.ThinkingConfig(
                    thinking_level="low",
                    include_thoughts=False
                )
            except Exception:
                pass

            response = await client.aio.models.generate_content_stream(
                model=model_name,
                contents=history[-1]["parts"][0]["text"],  # latest user message
                config=types.GenerateContentConfig(**config_kwargs),
            )

            async for chunk in response:
                token = ""
                if chunk.candidates:
                    for part in chunk.candidates[0].content.parts:
                        if part.text:
                            token += part.text
                if token:
                    collected_content.append(token)
                    payload = json.dumps({"token": token, "done": False})
                    yield f"data: {payload}\n\n"

            full_reply = "".join(collected_content)
            history.append({"role": "model", "parts": [{"text": full_reply}]})
            yield f"data: {json.dumps({'token': '', 'done': True})}\n\n"

        except Exception as exc:
            if history and history[-1].get("role") == "user":
                history.pop()
            error_payload = json.dumps({"error": str(exc), "done": True})
            yield f"data: {error_payload}\n\n"

    return StreamingResponse(
        token_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/session/{session_id}/history")
async def get_history(session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found.")
    # Convert to user-friendly format for the response
    return {
        "history": [
            {"role": msg["role"], "content": msg["parts"][0]["text"]}
            for msg in sessions[session_id]
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
