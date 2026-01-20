import os
import io
import base64
import json
import logging
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv

from gemini_client import GeminiClient

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="ElevenLabs <-> Gemini Proxy")

# CORS (Allow all for now, typical for server-to-server or development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Gemini Client
# We initialize it lazily or on startup. 
# Best practice: Initialize on startup to fail fast if key is missing.
gemini_client: Optional[GeminiClient] = None

@app.on_event("startup")
async def startup_event():
    global gemini_client
    try:
        gemini_client = GeminiClient()
        logger.info("Gemini Client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Gemini Client: {e}")
        # We don't exit here to allow the server to start, but requests will fail.

class ChatRequest(BaseModel):
    prompt: str
    stream: bool = False # Optional flag to enable streaming

@app.get("/")
async def root():
    return {"status": "ok", "service": "ElevenLabs-Gemini-Proxy"}

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Receives text prompt, sends to Gemini, returns Audio.
    Input: {"prompt": "Hello"}
    Output: {"audio": "base64_string"}
    """
    if not gemini_client:
        raise HTTPException(status_code=500, detail="Gemini Client is not initialized")
    
    logger.info(f"Received request: {request.prompt[:50]}...")

    try:
        # Generate Audio
        # Note: ElevenLabs usually expects a quick response.
        # If the user wants a STREAM of audio bytes for a "Custom LLM" WebSocket, 
        # that's a different protocol. But for a POST request, we return the full buffer 
        # or a chunked stream.
        
        # User requirement: "Return Gemini's raw audio (base64 encoded or binary)"
        # We'll default to returning a JSON with Base64 for the simplest integration.
        
        audio_data = await gemini_client.generate_response(request.prompt)
        
        if not audio_data:
             raise HTTPException(status_code=504, detail="No audio received from Gemini")

        # Encode to Base64
        audio_b64 = base64.b64encode(audio_data).decode('utf-8')
        
        return JSONResponse(content={
            "audio": audio_b64,
            "encoding": "base64",
            "format": "pcm" # Gemini native audio is typically PCM 24kHz
        })

    except Exception as e:
        logger.error(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
