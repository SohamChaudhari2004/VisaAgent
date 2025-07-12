import io
import logging
import os
from typing import Dict

import edge_tts

logger = logging.getLogger(__name__)

# Voice mappings for edge-tts
VOICE_MAPPINGS = {
    "VoiceA": "en-US-JennyNeural",
    "VoiceB": "en-US-ChristopherNeural",
    "VoiceC": "en-GB-SoniaNeural"
}

async def synthesize_tts(text: str, voice: str) -> bytes:
    """
    Use edge-tts to produce an audio payload.
    
    Args:
        text: The text to synthesize
        voice: Voice identifier from VOICE_MAPPINGS
        
    Returns:
        bytes: Audio data in MP3 format
    """
    try:
        # Map the voice selection to an edge-tts voice
        tts_voice = VOICE_MAPPINGS.get(voice, "en-US-JennyNeural")
        
        # Configure the TTS communication
        communicate = edge_tts.Communicate(text, tts_voice)
        
        # Stream to memory buffer
        stream = io.BytesIO()
        await communicate.stream_to_stream(stream)
        
        # Get the audio data
        stream.seek(0)
        audio_data = stream.read()
        
        logger.info(f"Synthesized {len(audio_data)} bytes of audio for text: '{text[:50]}...'")
        return audio_data
        
    except Exception as e:
        logger.error(f"TTS error: {str(e)}", exc_info=True)
        # Return an empty audio file in case of error
        return b''
