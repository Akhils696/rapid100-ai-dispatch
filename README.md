# RAPID-100 - Real-time AI for Priority Incident Dispatch

An AI-powered emergency call triage and routing system that transcribes calls in real-time, detects emergency types, assigns severity scores, extracts structured information, and routes to appropriate services.

## Features

- Real-time speech-to-text transcription using Whisper
- Emergency type detection (Fire, Medical, Crime, Accident, Disaster)
- Severity scoring (Critical, High, Medium, Low)
- Named Entity Recognition for location extraction
- Explainable AI with SHAP-based explanations
- Dispatcher dashboard with live call monitoring
- Structured logging for auditability
- Demo mode with simulated calls
- Call recording and storage functionality
- Enhanced Small Language Model (SLM) for improved classification
- Audio filtering and background noise extraction
- Comprehensive emergency call dataset for training

## Architecture

- Backend: Python with FastAPI
- Frontend: React with Tailwind CSS
- Speech-to-Text: OpenAI Whisper
- NLP Models: DistilBERT for classification
- Real-time communication: WebSocket

## Setup Instructions

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Install FFmpeg for audio processing:
   - Windows: Download from https://ffmpeg.org/download.html
   - macOS: `brew install ffmpeg`
   - Linux: `sudo apt install ffmpeg`
4. Set up environment variables in `.env` (see below)
5. Run the backend:
   ```bash
   cd backend && uvicorn main:app --reload
   ```
6. Run the frontend:
   ```bash
   cd frontend && npm install && npm run dev
   ```

## Environment Variables

The system uses several API keys and configuration options:

```bash
# Basic configuration
DEBUG=True
LOG_LEVEL=INFO
WHISPER_MODEL_SIZE=tiny
MAX_AUDIO_DURATION=300  # 5 minutes max
ENABLE_MOCK_SERVICES=True  # Set to False when deploying with real models
DATABASE_URL=sqlite:///./rapid100.db

# Enhanced features
OPENAI_API_KEY=your_openai_api_key_here  # For advanced Whisper API (optional)
HUGGINGFACE_API_KEY=your_huggingface_api_key_here  # For model downloads (optional)
AUDIO_FILTER_PRESET=noise_reduction_advanced  # Audio filtering preset
SLM_TRAINING_ENABLED=True  # Enable SLM training
```

## Enhanced Features

### Small Language Model (SLM)
The system now includes a specialized Small Language Model for emergency call classification that:
- Processes emergency-specific vocabulary
- Provides more accurate classifications for emergency scenarios
- Includes built-in training on emergency call datasets
- Offers better performance for domain-specific tasks

### Audio Filtering
The system includes advanced audio filtering capabilities:
- Real-time noise reduction
- Voice enhancement
- Background isolation
- Multiple filtering presets

### Call Recording
All emergency calls are automatically recorded and stored:
- WAV format for high quality
- Organized file naming with timestamps
- Automatic cleanup and organization
- Secure storage in dedicated directory

### Dataset
The system includes a comprehensive dataset of emergency calls for training and validation:
- 25 diverse emergency scenarios
- Multiple emergency types and severities
- Background noise variations
- Voice clarity and emotion intensity ratings

## API Endpoints

### Core Endpoints
- `GET /docs` - API Documentation
- `POST /api/classify` - Emergency classification
- `GET /api/logs` - Call logs
- `GET /api/simulate-call/{scenario}` - Simulate emergency calls

### Enhanced Endpoints
- `GET /api/recordings` - List all recorded calls
- `GET /recordings/{filename}` - Serve specific recording
- `POST /api/slm/process` - Process with Small Language Model
- `GET /api/audio/filters` - Get available audio filters

## Directory Structure

```
rapid100/
├── backend/
│   ├── api/
│   ├── models/
│   ├── services/
│   ├── utils/
│   ├── tests/
│   ├── slm_emergency_classifier.py  # NEW: Small Language Model
│   └── main.py
├── frontend/
├── logs/
├── data/
├── recordings/  # NEW: Call recordings storage
├── dataset/     # NEW: Training dataset
└── README.md
```