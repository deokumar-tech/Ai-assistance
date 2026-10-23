from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from main import process_text

app = FastAPI(title="Igris Assistant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class ChatRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)


class ChatResponse(BaseModel):
    response: str


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "online", "name": "Igris"}


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    text = request.text.strip()
    if not text:
        raise HTTPException(status_code=422, detail="Message cannot be empty.")
    return ChatResponse(response=process_text(text))
