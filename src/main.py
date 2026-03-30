import logging
import warnings

# langchain_core imports pydantic.v1 shims that are broken on Python 3.14+
warnings.filterwarnings(
    "ignore",
    message="Core Pydantic V1 functionality isn't compatible",
    category=UserWarning,
    module="langchain_core",
)

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .agent import analyze_mood
from .config import settings

logging.basicConfig(level=settings.log_level.upper())  # stdlib expects uppercase
logger = logging.getLogger(__name__)

if settings.log_level.upper() == "DEBUG":
    # Show raw HTTP calls to Ollama
    logging.getLogger("httpx").setLevel(logging.DEBUG)
    logging.getLogger("httpcore").setLevel(logging.DEBUG)

app = FastAPI(
    title="Mood AI Agent",
    description="Evaluates the mood of a person given a text input.",
    version="1.0.0",
)


class MoodRequest(BaseModel):
    text: str


class MoodResponse(BaseModel):
    input: str
    mood: str


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/analyze", response_model=MoodResponse)
def analyze(request: MoodRequest):
    if not request.text.strip():
        raise HTTPException(status_code=422, detail="Input text must not be empty.")
    logger.info("Analyzing mood for input: %s", request.text[:80])
    mood = analyze_mood(request.text)
    return MoodResponse(input=request.text, mood=mood)


if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=True,
        log_level=settings.log_level.lower(),  # uvicorn expects lowercase
        reload_dirs=["."],
    )
