# SRVISA - Audio-based Visa Interview Training

SRVISA is an interactive application that simulates visa interviews using speech recognition and AI-generated questions. It helps users practice for their visa interviews in a realistic setting.

## Features

- Audio-based interview simulation with AI-generated questions
- Multiple visa types supported (tourist, student)
- Choice of AI voices for the interviewer
- Real-time audio recording and processing
- Automatic evaluation of interview performance
- Detailed feedback on fluency, confidence, content accuracy, and response time

## Tech Stack

### Backend

- Python 3.11
- FastAPI
- WebSockets for real-time audio streaming
- edge-tts for text-to-speech
- Whisper API for speech-to-text
- WebRTC VAD for voice activity detection
- ChromaDB for vector storage
- Mistral LLM API for question generation and evaluation

### Frontend

- React with Vite
- WebSockets for real-time communication
- Web Audio API for audio recording and playback
- Context API for state management

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- npm or yarn

### Backend Setup

1. Navigate to the backend directory:

   ```bash
   cd backend
   ```

2. Create a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Create a .env file from the example:

   ```bash
   cp .env.example .env
   ```

5. Edit the .env file with your API keys:

   ```env
   MISTRAL_API_KEY=your_mistral_api_key_here
   WHISPER_API_KEY=your_whisper_api_key_here
   CHROMA_DB_PATH=./data/chromadb
   ```

6. Start the backend server:

   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

### Frontend Setup

1. Navigate to the client directory:

   ```bash
   cd client
   ```

2. Install dependencies:

   ```bash
   npm install
   ```

3. Start the development server:

   ```bash
   npm run dev
   ```

4. Open your browser and navigate to http://localhost:5173

## Usage

1. Select your visa type (tourist or student)
2. Choose your preferred AI voice
3. Select your subscription tier (determines number of questions)
4. Click "Start Interview"
5. Listen to each question and respond naturally
6. After all questions, review your performance metrics and feedback

## Project Structure

```
/backend
  /app
    __init__.py
    main.py         # FastAPI app + WebSocket endpoint
    tts.py          # edge-tts wrapper
    asr.py          # Whisper wrapper
    vad.py          # VAD helper
    rag.py          # Chroma + Mistral
    evaluation.py   # scoring logic
  requirements.txt
  .env.example
/client
  /public
  /src
    /assets
    /components
    /context
    /hooks
    App.jsx
    main.jsx
  package.json
  vite.config.js
```

## License

MIT
