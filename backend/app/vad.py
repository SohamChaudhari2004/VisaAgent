import asyncio
import logging
from typing import AsyncIterable, List, Optional

import webrtcvad
from fastapi import WebSocket

logger = logging.getLogger(__name__)

# Initialize VAD
vad = webrtcvad.Vad(3)  # Aggressiveness level 3 (highest)
SAMPLE_RATE = 16000
FRAME_DURATION_MS = 30  # Frame duration in milliseconds

async def detect_end_of_speech(websocket: WebSocket) -> AsyncIterable[bytes]:
    """
    Use webrtcvad to detect when to stop recording.
    
    Args:
        websocket: WebSocket connection to receive audio chunks
        
    Yields:
        bytes: Audio chunks until end of speech is detected
    """
    silence_frames = 0
    max_silence_frames = 50  # About 1.5 seconds of silence
    
    try:
        # Process incoming audio frames
        while True:
            # Receive audio frame from WebSocket
            data = await websocket.receive_bytes()
            
            if not data:
                break
            
            # Yield the data
            yield data
            
            # Check if this is a valid frame for VAD
            if len(data) < 320:  # Minimum size for a 16kHz, 20ms frame
                continue
                
            # Check for voice activity
            try:
                is_speech = vad.is_speech(data[:320], SAMPLE_RATE)
                
                if is_speech:
                    # Reset silence counter
                    silence_frames = 0
                else:
                    # Increment silence counter
                    silence_frames += 1
                    
                # If we've reached the silence threshold, stop
                if silence_frames >= max_silence_frames:
                    logger.info("End of speech detected after silence threshold")
                    break
                    
            except Exception as e:
                logger.warning(f"VAD processing error: {str(e)}")
                # Continue even if VAD fails
                
    except Exception as e:
        logger.error(f"Error in speech detection: {str(e)}", exc_info=True)
