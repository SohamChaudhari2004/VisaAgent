import asyncio
import json
import logging
import os
import traceback
from datetime import datetime
from typing import Dict, List, Tuple, Optional

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .tts import synthesize_tts
from .asr import whisper_transcribe
from .vad import detect_end_of_speech
from .rag import retrieve_question_from_chroma
from .evaluation import evaluate_session

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Update the app initialization to include a prefix
app = FastAPI(
    title="SRVISA API", 
    description="Audio-based Visa Interview Training API"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@app.websocket("/ws/health")
async def health_websocket(websocket: WebSocket):
    """WebSocket health check endpoint."""
    await websocket.accept()
    try:
        await websocket.send_json({
            "status": "ok",
            "timestamp": datetime.now().isoformat()
        })
    finally:
        await websocket.close()

class InterviewSession:
    """Track the state of an interview session."""
    
    def __init__(self, visa_type: str, voice: str, question_count: int):
        self.visa_type = visa_type
        self.voice = voice
        self.remaining_questions = question_count
        self.session_log: List[Tuple[str, str, datetime]] = []
        self.current_question: Optional[str] = None

@app.websocket("/ws/agent")
async def interview_agent(websocket: WebSocket):
    """WebSocket endpoint for the interview agent."""
    await websocket.accept()
    
    try:
        # Receive initial configuration
        init_data = await websocket.receive_text()
        config = json.loads(init_data)
        
        visa_type = config.get("visaType", "tourist")
        voice = config.get("voice", "VoiceA")
        question_count = config.get("questionCount", 5)
        
        logger.info(f"Starting interview session: {visa_type=}, {voice=}, {question_count=}")
        
        # Initialize session
        session = InterviewSession(visa_type, voice, question_count)
        
        # Main interview loop
        while session.remaining_questions > 0:
            try:
                # 1. Retrieve question
                logger.debug("Retrieving next question from ChromaDB")
                question = await retrieve_question_from_chroma(visa_type)
                session.current_question = question
                logger.info(f"Retrieved question: {question}")
                
                # Send question text to client
                await websocket.send_text(json.dumps({"question": question}))
                
                # 2. Synthesize speech and send audio
                logger.debug(f"Synthesizing speech for question using {voice}")
                audio_bytes = await synthesize_tts(question, voice)
                logger.debug(f"Sending audio bytes: {len(audio_bytes)} bytes")
                await websocket.send_bytes(audio_bytes)
                
                # 3. Start recording
                logger.debug("Sending start_record command")
                await websocket.send_text(json.dumps({"cmd": "start_record"}))
                
                # 4. Collect audio chunks until end of speech
                audio_chunks = []
                logger.debug("Waiting for audio chunks")
                async for chunk in detect_end_of_speech(websocket):
                    audio_chunks.append(chunk)
                    logger.debug(f"Received audio chunk: {len(chunk)} bytes")
                
                if not audio_chunks:
                    logger.warning("No audio received")
                    continue
                
                # Combine audio chunks
                full_audio = b''.join(audio_chunks)
                logger.debug(f"Combined audio size: {len(full_audio)} bytes")
                
                # 5. Transcribe the answer
                logger.debug("Transcribing audio")
                answer_text = await whisper_transcribe(full_audio)
                logger.info(f"Transcribed answer: {answer_text}")
                
                # 6. Record and acknowledge
                timestamp = datetime.now()
                session.session_log.append((question, answer_text, timestamp))
                session.remaining_questions -= 1
                
                await websocket.send_text(json.dumps({
                    "cmd": "ack",
                    "answerText": answer_text
                }))
                
                # Small delay between questions
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error during question processing: {str(e)}")
                logger.error(traceback.format_exc())
                await websocket.send_text(json.dumps({
                    "cmd": "error",
                    "message": f"Error processing question: {str(e)}"
                }))
                # Don't exit the loop, try the next question
        
        # Evaluate session
        try:
            logger.debug("Evaluating session")
            metrics, feedback = await evaluate_session(session.session_log)
            logger.info(f"Session completed. Metrics: {metrics}")
            
            # Send final feedback
            await websocket.send_text(json.dumps({
                "cmd": "complete",
                "metrics": metrics,
                "feedback": feedback
            }))
        except Exception as e:
            logger.error(f"Error evaluating session: {str(e)}")
            logger.error(traceback.format_exc())
            await websocket.send_text(json.dumps({
                "cmd": "error",
                "message": f"Error evaluating session: {str(e)}"
            }))
        
    except WebSocketDisconnect:
        logger.warning("WebSocket disconnected")
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {str(e)}")
        await websocket.send_text(json.dumps({
            "cmd": "error",
            "message": f"Invalid JSON format: {str(e)}"
        }))
    except Exception as e:
        logger.error(f"Error in WebSocket: {str(e)}")
        logger.error(traceback.format_exc())
        try:
            await websocket.send_text(json.dumps({
                "cmd": "error",
                "message": "An error occurred during the interview."
            }))
        except:
            logger.error("Could not send error message to client")

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
    