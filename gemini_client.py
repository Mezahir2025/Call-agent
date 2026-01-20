import os
import asyncio
import base64
import json
import logging
from google import genai
from google.genai import types

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeminiClient:
    def __init__(self):
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            logger.error("GEMINI_API_KEY not found in environment variables")
            raise ValueError("GEMINI_API_KEY is required")
        
        self.client = genai.Client(api_key=api_key, http_options={"api_version": "v1alpha"})
        self.model_name = "gemini-2.0-flash-exp" # Switching to confirmed Live API model
        self.voice_name = "Aoede" # Example typical voice, but we'll try to configure for Azerbaijani if possible via prompt since config is limited in preview
        
    async def generate_response(self, text_input: str):
        """
        Connects to Gemini Live, sends text, and returns the accumulated audio.
        """
        audio_chunks = []
        
        config = types.LiveConnectConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=self.voice_name
                    )
                )
            ),
             system_instruction=types.Content(
                parts=[
                    types.Part(text="You are a helpful assistant. You confirm receiving the message and reply in Azerbaijani. Speak naturally.")
                ]
            ),
        )

        try:
            async with self.client.aio.live.connect(model=self.model_name, config=config) as session:
                # Send text input
                await session.send(input=text_input, end_of_turn=True)
                
                # Receive responses
                async for response in session.receive():
                    if response.server_content:
                        model_turn = response.server_content.model_turn
                        if model_turn:
                            for part in model_turn.parts:
                                if part.inline_data:
                                    audio_chunks.append(part.inline_data.data)
                        
                        if response.server_content.turn_complete:
                            break
                            
            # Combine audio chunks
            full_audio = b"".join(audio_chunks)
            return full_audio

        except Exception as e:
            logger.error(f"Error in Gemini Live generation: {e}")
            raise

    async def generate_response_stream(self, text_input: str):
        """
        Yields audio chunks as they arrive.
        """
        config = types.LiveConnectConfig(
            response_modalities=["AUDIO"],
             speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=self.voice_name
                    )
                )
            ),
            system_instruction=types.Content(
                parts=[
                    types.Part(text="You are a helpful assistant. Reply in Azerbaijani. Keep it relatively short and conversational.")
                ]
            ),
        )

        try:
            async with self.client.aio.live.connect(model=self.model_name, config=config) as session:
                await session.send(input=text_input, end_of_turn=True)
                
                async for response in session.receive():
                    if response.server_content is None:
                        continue
                        
                    model_turn = response.server_content.model_turn
                    if model_turn:
                        for part in model_turn.parts:
                            if part.inline_data:
                                yield part.inline_data.data
                    
                    if response.server_content.turn_complete:
                        break
                        
        except Exception as e:
            logger.error(f"Error in Gemini Live stream: {e}")
            raise
