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

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    prompt: Optional[str] = None
    messages: Optional[List[Message]] = None
    stream: bool = False

@app.get("/")
async def root():
    return {"status": "ok", "service": "ElevenLabs-Gemini-Proxy"}

@app.post("/chat/completions")
@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Receives text prompt (or OpenAI style messages), sends to Gemini, returns Audio.
    Input: {"prompt": "Hello"} OR {"messages": [{"role": "user", "content": "Hello"}]}
    Output: {"audio": "base64_string"}
    """
    if not gemini_client:
        raise HTTPException(status_code=500, detail="Gemini Client is not initialized")
    
    # Extract text from prompt or messages
    text_input = ""
    if request.prompt:
        text_input = request.prompt
    elif request.messages and len(request.messages) > 0:
        text_input = request.messages[-1].content
    
    if not text_input:
         raise HTTPException(status_code=400, detail="No prompt or messages provided")

    logger.info(f"Received request: {text_input[:50]}...")

    try:
        audio_data = await gemini_client.generate_response(text_input)
        
        if not audio_data:
             raise HTTPException(status_code=504, detail="No audio received from Gemini")

        # Encode to Base64
        audio_b64 = base64.b64encode(audio_data).decode('utf-8')
        
        # Return strict structure if needed, but keeping simple JSON for now as requested
        return JSONResponse(content={
            "audio": audio_b64,
            "encoding": "base64",
            "format": "pcm"
        })

    except Exception as e:
        logger.error(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
