import io
import logging
import os
import tempfile
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# Get Groq API key from environment
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

async def whisper_transcribe(audio: bytes) -> str:
    """
    Send audio data to Groq's Whisper API and return transcript.
    
    Args:
        audio: Audio data bytes
        
    Returns:
        str: Transcribed text
    """
    if not GROQ_API_KEY:
        logger.warning("GROQ_API_KEY not set, using fallback transcription")
        return "I'm sorry, I couldn't transcribe your answer properly."
    
    if not audio or len(audio) < 100:
        logger.warning(f"Audio data too small ({len(audio) if audio else 0} bytes), using fallback")
        return "I'm sorry, I couldn't transcribe your answer properly."
    
    try:
        # Save audio to a temporary file
        logger.debug(f"Saving {len(audio)} bytes to temporary file")
        with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as temp_file:
            temp_file.write(audio)
            temp_file_path = temp_file.name
        
        logger.debug(f"Temporary file created: {temp_file_path}")
        
        try:
            # Use httpx instead of the Groq client for more control
            async with httpx.AsyncClient(timeout=30.0) as client:
                logger.debug("Sending audio to Groq API")
                
                # Prepare multipart form
                with open(temp_file_path, "rb") as file:
                    files = {"file": (os.path.basename(temp_file_path), file.read(), "audio/webm")}
                    
                    response = await client.post(
                        "https://api.groq.com/openai/v1/audio/transcriptions",
                        headers={
                            "Authorization": f"Bearer {GROQ_API_KEY}"
                        },
                        data={
                            "model": "whisper-large-v3-turbo",
                            "response_format": "text"
                        },
                        files=files
                    )
                
                if response.status_code != 200:
                    logger.error(f"Groq API error: {response.status_code} - {response.text}")
                    return "I'm sorry, I couldn't transcribe your answer properly."
                
                # Extract transcript from response
                transcript = response.text.strip()
                logger.info(f"Transcription successful: {transcript[:50]}...")
                return transcript
                
        except httpx.TimeoutException:
            logger.error("Groq API request timed out")
            return "I'm sorry, I couldn't transcribe your answer properly."
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
                logger.debug(f"Temporary file removed: {temp_file_path}")
    
    except Exception as e:
        logger.error(f"Transcription error: {str(e)}", exc_info=True)
        return "I'm sorry, I couldn't transcribe your answer properly."
