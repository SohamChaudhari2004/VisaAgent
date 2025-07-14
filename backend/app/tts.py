import io
import logging
import os
from typing import Dict

import edge_tts

logger = logging.getLogger(__name__)

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
        tts_voice = VOICE_MAPPINGS.get(voice, "en-US-JennyNeural")
        communicate = edge_tts.Communicate(text, tts_voice)
        # Use a temporary file to save the MP3, then read it back
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmpfile:
            tmpfile_path = tmpfile.name
        try:
            await communicate.save(tmpfile_path)
            with open(tmpfile_path, "rb") as f:
                audio_data = f.read()
        finally:
            if os.path.exists(tmpfile_path):
                os.remove(tmpfile_path)
        logger.info(f"Synthesized {len(audio_data)} bytes of audio for text: '{text[:50]}...'")
        return audio_data
    except Exception as e:
        logger.error(f"TTS error: {str(e)}", exc_info=True)
        return b''
        return audio_data
        
    except Exception as e:
        logger.error(f"TTS error: {str(e)}", exc_info=True)
        # Return an empty audio file in case of error
        return b''
