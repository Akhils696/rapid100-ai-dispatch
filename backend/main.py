from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional
import wave
import pydub
from pydub import AudioSegment

from services.transcription_service import TranscriptionService
from services.classification_service import ClassificationService
from services.severity_service import SeverityService
from services.location_service import LocationService
from services.explanation_service import ExplanationService
from models.call_data import CallData, EmergencyType, SeverityLevel, RoutingDecision, LocationData
from slm_emergency_classifier import EmergencyCallSLM
from knowledge_base import get_knowledge_base


class CallRecorder:
    def __init__(self, call_id: str):
        self.call_id = call_id
        self.audio_segments = []
        self.recording_directory = "recordings"
        os.makedirs(self.recording_directory, exist_ok=True)
    
    def add_audio_segment(self, audio_data: bytes):
        """Add an audio segment to the recording"""
        self.audio_segments.append(audio_data)
    
    def save_recording(self):
        """Combine all segments and save the complete recording"""
        if not self.audio_segments:
            return None
            
        # Combine all audio segments
        combined_audio = AudioSegment.empty()
        for segment in self.audio_segments:
            try:
                # Convert bytes to AudioSegment
                audio_segment = AudioSegment.from_raw(
                    data=segment,
                    sample_width=2,  # Assuming 16-bit audio
                    frame_rate=16000,  # Assuming 16kHz sample rate
                    channels=1       # Assuming mono
                )
                combined_audio += audio_segment
            except Exception as e:
                logging.error(f"Error adding audio segment: {e}")
                continue
        
        # Export the combined audio
        filename = f"{self.recording_directory}/call_{self.call_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.wav"
        combined_audio.export(filename, format="wav")
        
        logging.info(f"Saved call recording: {filename}")
        return filename


# Store active connections and recorders
active_connections: Dict[str, WebSocket] = {}
active_recordings: Dict[str, CallRecorder] = {}

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/calls.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="RAPID-100 - AI Emergency Call Triage System", 
              description="Real-time AI for Priority Incident Dispatch",
              version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import os
USE_MOCK_SERVICES = os.getenv("ENABLE_MOCK_SERVICES", "True").lower() == "true"

# Initialize services
if USE_MOCK_SERVICES:
    print("Using mock services for faster startup")
    transcription_service = TranscriptionService()
    classification_service = None
    severity_service = None
    location_service = None
    explanation_service = None
    slm = None
    knowledge_base = None
else:
    print("Using full services")
    transcription_service = TranscriptionService()
    classification_service = ClassificationService()
    severity_service = SeverityService()
    location_service = LocationService()
    explanation_service = ExplanationService()
    
    # Initialize SLM
    slm = EmergencyCallSLM()
    try:
        slm.train()
        print("SLM loaded and trained successfully")
    except Exception as e:
        print(f"Error loading SLM: {e}")
        print("Using rule-based fallback")
    
    # Initialize knowledge base
    knowledge_base = get_knowledge_base()

# Store active connections
active_connections: Dict[str, WebSocket] = {}


@app.on_event("startup")
async def startup_event():
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    logger.info("RAPID-100 system started")
    if not USE_MOCK_SERVICES and knowledge_base:
        logger.info(f"Knowledge base initialized with {knowledge_base.get_statistics()} entries")
    else:
        logger.info("Running in mock mode - knowledge base disabled")

@app.websocket("/ws/transcribe/{call_id}")
async def websocket_transcribe(websocket: WebSocket, call_id: str):
    await websocket.accept()
    active_connections[call_id] = websocket
    
    # Create a call recorder for this call
    call_recorder = CallRecorder(call_id)
    active_recordings[call_id] = call_recorder
    
    # Initialize call parameters
    current_language = "en"
    noise_filtering_enabled = True
    sample_rate = 48000
    audio_level = 0.0
    
    try:
        while True:
            # Receive data from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle configuration messages
            if message.get("type") == "config":
                current_language = message.get("language", "en")
                noise_filtering_enabled = message.get("noise_filtering", True)
                sample_rate = message.get("sample_rate", 48000)
                logger.info(f"Call {call_id} configured: language={current_language}, noise_filtering={noise_filtering_enabled}")
                continue
            
            # Handle audio chunks
            elif message.get("type") == "audio_chunk":
                # Convert data back to bytes
                audio_data = bytes(message["data"])
                audio_level = message.get("audio_level", 0)
                timestamp = message.get("timestamp")
                
                # Add audio data to recording
                call_recorder.add_audio_segment(audio_data)
                
                # Process audio chunk with enhanced parameters
                transcription = await transcription_service.process_audio_chunk(
                    audio_data, 
                    language=current_language,
                    noise_filtering=noise_filtering_enabled,
                    sample_rate=sample_rate,
                    audio_level=audio_level
                )
                            
                if transcription.strip():
                    if USE_MOCK_SERVICES:
                        # Mock service responses - dynamically determine type and severity based on content
                        text_lower = transcription.lower()
                        
                        # Determine emergency type based on keywords in transcription
                        if any(keyword in text_lower for keyword in ['fire', 'smoke', 'burn', 'flame']):
                            emergency_type = EmergencyType.FIRE
                        elif any(keyword in text_lower for keyword in ['police', 'crime', 'gun', 'shot', 'break', 'robbery', 'assault']):
                            emergency_type = EmergencyType.CRIME
                        elif any(keyword in text_lower for keyword in ['accident', 'crash', 'collision', 'car', 'hit']):
                            emergency_type = EmergencyType.ACCIDENT
                        elif any(keyword in text_lower for keyword in ['weather', 'tornado', 'hurricane', 'flood', 'earthquake']):
                            emergency_type = EmergencyType.DISASTER
                        else:
                            emergency_type = EmergencyType.MEDICAL  # Default to medical
                        
                        # Determine severity based on keywords in transcription
                        if any(keyword in text_lower for keyword in ['unconscious', 'not breathing', 'heart attack', 'stroke', 'dying', 'critical']):
                            severity = SeverityLevel.CRITICAL
                        elif any(keyword in text_lower for keyword in ['injury', 'accident', 'fire', 'urgent', 'emergency', 'gunshot']):
                            severity = SeverityLevel.HIGH
                        elif any(keyword in text_lower for keyword in ['sick', 'minor', 'small', 'little']):
                            severity = SeverityLevel.LOW
                        else:
                            severity = SeverityLevel.MEDIUM  # Default to medium
                        
                        # Generate mock location based on emergency type
                        location_areas = {
                            "MEDICAL": ["Downtown Hospital", "City Medical Center", "Emergency Room", "Health Plaza"],
                            "FIRE": ["Residential Area", "Industrial District", "Suburban Neighborhood", "Commercial Complex"],
                            "CRIME": ["Downtown", "Residential Street", "Shopping District", "Industrial Area"],
                            "ACCIDENT": ["Highway 101", "Main Street", "Intersection", "Highway Exit 15"],
                            "DISASTER": ["Downtown", "Residential Area", "Industrial Zone", "Coastal Region"]
                        }
                        
                        location_options = location_areas.get(emergency_type.value, ["Unknown Location"])
                        import random
                        location = random.choice(location_options)
                        
                        explanation = "Mock explanation for testing"
                        routing_decision = RoutingDecision(
                            department=get_department_for_emergency(emergency_type),
                            confidence=0.8
                        )
                        slm_result = {
                            'emergency_type': emergency_type.value,
                            'severity': severity.value,
                            'emotion_intensity': 0.7,
                            'confidence': 0.8,
                            'features': {}
                        }
                        similar_scenarios = []
                        relevant_procedures = []
                    else:
                        # Use SLM for enhanced classification
                        slm_result = slm.predict_call_details(transcription)
                        emergency_type = EmergencyType(slm_result['emergency_type'])
                        severity = SeverityLevel(slm_result['severity'])
                                    
                        # Use knowledge base to find similar scenarios and enhance analysis
                        similar_scenarios = knowledge_base.search_similar_scenarios(transcription, n_results=3)
                                    
                        # Use knowledge base to find relevant procedures
                        relevant_procedures = knowledge_base.search_procedures(f"{emergency_type.value} {transcription}", n_results=2)
                                    
                        # Extract location
                        location = location_service.extract_location(transcription)
                                    
                        # Generate explanation
                        explanation = explanation_service.generate_explanation(transcription, emergency_type, severity)
                                    
                        # Create routing decision
                        routing_decision = RoutingDecision(
                            department=get_department_for_emergency(emergency_type),
                            confidence=slm_result.get('confidence', 0.9)
                        )
                                
                    # Calculate enhanced audio metrics
                    noise_confidence = calculate_audio_quality(audio_data, audio_level, transcription)
                    emotion_meter = slm_result.get('emotion_intensity', 0.5)
                                
                    # Create location data object
                    location_obj = LocationData(
                        latitude=location_data["latitude"],
                        longitude=location_data["longitude"],
                        area=location_data["area"]
                    )
                                    
                    # Log the call data
                    call_data = CallData(
                        call_id=call_id,
                        timestamp=datetime.utcnow(),
                        transcript=transcription,
                        predicted_class=emergency_type,
                        severity=severity,
                        routing_decision=routing_decision,
                        confidence=slm_result.get('confidence', 0.9),
                        explanation=explanation,
                        location=location,
                        location_data=location_obj,
                        emotion_meter=emotion_meter,
                        noise_confidence=noise_confidence,
                        extracted_entities=slm_result['features'],
                        language=current_language,
                        audio_quality_metrics={
                            "audio_level": audio_level,
                            "noise_filtering": noise_filtering_enabled,
                            "sample_rate": sample_rate
                        }
                    )
                                
                    log_call_data(call_data)
                                
                    # Generate mock location coordinates for demonstration
                    location_data = generate_mock_location(location, emergency_type.value)
                                    
                    # Send response back to client
                    response = {
                        "transcript": transcription,
                        "emergency_type": emergency_type.value,
                        "severity": severity.value,
                        "location": location,
                        "location_data": location_data,
                        "routing_decision": routing_decision.dict(),
                        "explanation": explanation,
                        "emotion_meter": emotion_meter,
                        "noise_confidence": noise_confidence,
                        "confidence": slm_result.get('confidence', 0.9),
                        "language": current_language,
                        "timestamp": datetime.utcnow().isoformat(),
                        "audio_metrics": {
                            "level": audio_level,
                            "quality_score": noise_confidence
                        },
                        "similar_scenarios": [scenario['metadata'] for scenario in similar_scenarios] if not USE_MOCK_SERVICES else [],
                        "relevant_procedures": [proc for proc in relevant_procedures] if not USE_MOCK_SERVICES else []
                    }
                    
                    await websocket.send_json(response)
            
    except WebSocketDisconnect:
        logger.info(f"Call {call_id} disconnected")
        
        # Save the recording when the call ends
        if call_id in active_recordings:
            recording_path = active_recordings[call_id].save_recording()
            if recording_path:
                logger.info(f"Recording saved: {recording_path}")
            # Remove the recorder
            del active_recordings[call_id]
        
        # Add the call to the knowledge base for future reference
        if transcription and emergency_type and severity:
            knowledge_base.add_emergency_scenario(
                transcript=transcription,
                emergency_type=emergency_type.value,
                severity=severity.value,
                location=location if location else "Unknown",
                background_noise=slm_result.get('background_noise', 'Unknown'),
                emotion_intensity=slm_result.get('emotion_intensity', 0.0)
            )
        
        if call_id in active_connections:
            del active_connections[call_id]
    except Exception as e:
        logger.error(f"Error processing call {call_id}: {str(e)}")
        # Ensure recording is saved even if there's an error
        if call_id in active_recordings:
            recording_path = active_recordings[call_id].save_recording()
            if recording_path:
                logger.info(f"Recording saved: {recording_path}")
            del active_recordings[call_id]
        await websocket.close()

# Helper function to generate mock location coordinates
def generate_mock_location(location_text: str, emergency_type: str) -> dict:
    """Generate mock latitude and longitude coordinates based on location description"""
    # Base coordinates for different areas
    areas = {
        "downtown": {"lat": 40.7128, "lng": -74.0060},
        "suburbia": {"lat": 40.7589, "lng": -73.9851},
        "residential": {"lat": 40.7505, "lng": -73.9934},
        "industrial": {"lat": 40.7282, "lng": -74.0776},
        "highway": {"lat": 37.7749, "lng": -122.4194},
        "main street": {"lat": 40.7128, "lng": -74.0060},
        "oak ave": {"lat": 40.7589, "lng": -73.9851},
        "pine rd": {"lat": 40.7505, "lng": -73.9934},
        "default": {"lat": 40.7128, "lng": -74.0060}
    }
    
    # Match location text to area
    location_lower = location_text.lower() if location_text else ""
    area_key = "default"
    
    for area in areas:
        if area in location_lower:
            area_key = area
            break
    
    base_coords = areas[area_key]
    
    # Add small random offset for variety
    import random
    lat_offset = random.uniform(-0.01, 0.01)
    lng_offset = random.uniform(-0.01, 0.01)
    
    return {
        "latitude": round(base_coords["lat"] + lat_offset, 6),
        "longitude": round(base_coords["lng"] + lng_offset, 6),
        "area": area_key.title()
    }

# Helper function to calculate audio quality
def calculate_audio_quality(audio_data: bytes, audio_level: float, transcription: str) -> float:
    """Calculate audio quality score based on multiple factors"""
    quality_score = 0.0
    
    # Factor 1: Audio level consistency (30% weight)
    if 0.1 <= audio_level <= 0.9:  # Good audio level range
        quality_score += 0.3
    elif audio_level > 0.01:  # Detectable audio
        quality_score += 0.15
    
    # Factor 2: Transcription length and content (40% weight)
    if len(transcription) > 10:  # Meaningful transcription
        quality_score += 0.2
        if len(transcription) > 50:  # Good length
            quality_score += 0.2
        
        # Check for common transcription artifacts that indicate poor quality
        noisy_patterns = ['uh', 'um', 'ah', 'you know', 'like', 'so']
        noise_count = sum(1 for pattern in noisy_patterns if pattern in transcription.lower())
        noise_penalty = min(noise_count * 0.05, 0.2)
        quality_score -= noise_penalty
    
    # Factor 3: Audio data characteristics (30% weight)
    if len(audio_data) > 1000:  # Sufficient audio data
        quality_score += 0.15
    if len(audio_data) > 5000:  # Good amount of data
        quality_score += 0.15
    
    return max(0.0, min(1.0, quality_score))

def get_department_for_emergency(emergency_type: EmergencyType) -> str:
    """Map emergency type to appropriate department"""
    mapping = {
        EmergencyType.FIRE: "Fire Department",
        EmergencyType.MEDICAL: "Ambulance Service",
        EmergencyType.CRIME: "Police Department",
        EmergencyType.ACCIDENT: "Emergency Services",
        EmergencyType.DISASTER: "Emergency Management",
        EmergencyType.UNKNOWN: "General Emergency"
    }
    return mapping.get(emergency_type, "General Emergency")

def log_call_data(call_data: CallData):
    """Log call data for auditability"""
    log_entry = {
        "call_id": call_data.call_id,
        "timestamp": call_data.timestamp.isoformat(),
        "transcript": call_data.transcript,
        "predicted_class": call_data.predicted_class.value,
        "severity": call_data.severity.value,
        "routing_decision": call_data.routing_decision.dict(),
        "confidence": call_data.confidence,
        "explanation": call_data.explanation
    }
    
    with open("logs/calls.json", "a") as f:
        f.write(json.dumps(log_entry) + "\n")
    
    logger.info(f"Logged call {call_data.call_id}")

@app.post("/api/classify")
async def classify_emergency(request: dict):
    """Classify emergency from text input"""
    text = request.get("text", "")
    if not text:
        raise HTTPException(status_code=400, detail="Text is required")
    
    emergency_type = classification_service.classify_emergency(text)
    severity = severity_service.calculate_severity(text)
    location = location_service.extract_location(text)
    explanation = explanation_service.generate_explanation(text, emergency_type, severity)
    
    routing_decision = RoutingDecision(
        department=get_department_for_emergency(emergency_type),
        confidence=0.9  # Placeholder
    )
    
    result = {
        "emergency_type": emergency_type.value,
        "severity": severity.value,
        "location": location,
        "routing_decision": routing_decision.dict(),
        "explanation": explanation
    }
    
    return result

@app.get("/api/simulate-call/{scenario}")
async def simulate_call(scenario: str):
    """Simulate an emergency call scenario"""
    scenarios = {
        "medical": {
            "text": "Help! My wife is unconscious and not breathing. She collapsed suddenly. Address is 123 Main St, Downtown. Please send an ambulance immediately!",
            "expected_type": "MEDICAL",
            "expected_severity": "CRITICAL"
        },
        "fire": {
            "text": "There's a fire at my house! Smoke is everywhere, flames coming from the kitchen. Address is 456 Oak Ave, Suburbia. Need firefighters now!",
            "expected_type": "FIRE",
            "expected_severity": "HIGH"
        },
        "crime": {
            "text": "Someone is breaking into my house! I hear glass breaking and footsteps. Address is 789 Pine Rd, Residential Area. Gunshots fired. Police needed immediately!",
            "expected_type": "CRIME",
            "expected_severity": "HIGH"
        },
        "accident": {
            "text": "Car accident on Highway 101 near Exit 15. Multiple cars involved, people injured. Blood everywhere. Need ambulances and police.",
            "expected_type": "ACCIDENT",
            "expected_severity": "CRITICAL"
        },
        "disaster": {
            "text": "Tornado warning! Severe weather approaching downtown. Taking shelter in basement. Large debris flying. Need emergency management.",
            "expected_type": "DISASTER",
            "expected_severity": "CRITICAL"
        }
    }
    
    if scenario not in scenarios:
        raise HTTPException(status_code=404, detail="Scenario not found")
    
    scenario_data = scenarios[scenario]
    text = scenario_data["text"]
    
    if USE_MOCK_SERVICES:
        # Mock service responses
        emergency_type = EmergencyType(scenario_data["expected_type"])  # Use expected type directly
        severity = SeverityLevel(scenario_data["expected_severity"])  # Use expected severity from scenario
        # Generate appropriate location based on scenario
        location_areas = {
            "medical": "Downtown Hospital",
            "fire": "Residential Area",
            "crime": "Downtown",
            "accident": "Highway 101",
            "disaster": "Downtown"
        }
        location = location_areas.get(scenario, "Unknown Location")
        explanation = f"Mock simulation for {scenario} emergency"
        routing_decision = RoutingDecision(
            department=get_department_for_emergency(emergency_type),
            confidence=0.8
        )
    else:
        # Real service responses
        emergency_type = classification_service.classify_emergency(text)
        severity = severity_service.calculate_severity(text)
        location = location_service.extract_location(text)
        explanation = explanation_service.generate_explanation(text, emergency_type, severity)
        
        routing_decision = RoutingDecision(
            department=get_department_for_emergency(emergency_type),
            confidence=0.9
        )
    
    # Generate location coordinates
    location_coords = generate_mock_location(location, emergency_type.value)
    location_obj = LocationData(
        latitude=location_coords["latitude"],
        longitude=location_coords["longitude"],
        area=location_coords["area"]
    )
    
    result = {
        "scenario": scenario,
        "input_text": text,
        "predicted_type": emergency_type.value,
        "severity": severity.value,
        "location": location,
        "location_data": {
            "latitude": location_obj.latitude,
            "longitude": location_obj.longitude,
            "area": location_obj.area
        },
        "routing_decision": routing_decision.dict(),
        "explanation": explanation,
        "expected_type": scenario_data["expected_type"]
    }
    
    return result

@app.get("/api/logs")
async def get_logs():
    """Retrieve call logs"""
    logs = []
    try:
        with open("logs/calls.json", "r") as f:
            for line in f:
                if line.strip():
                    logs.append(json.loads(line))
    except FileNotFoundError:
        pass
    
    return {"logs": logs[-50:]}  # Return last 50 logs

@app.get("/api/recordings")
async def get_recordings():
    """Get list of all recorded calls"""
    recordings_dir = "recordings"
    if not os.path.exists(recordings_dir):
        return {"recordings": []}
    
    recording_files = []
    for filename in os.listdir(recordings_dir):
        if filename.endswith('.wav'):
            filepath = os.path.join(recordings_dir, filename)
            stat = os.stat(filepath)
            recording_files.append({
                "filename": filename,
                "size": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "url": f"/recordings/{filename}"
            })
    
    return {"recordings": recording_files}


@app.get("/recordings/{filename}")
async def get_recording(filename: str):
    """Serve a specific recording file"""
    import os
    from fastapi.responses import FileResponse
    
    filepath = os.path.join("recordings", filename)
    if not os.path.exists(filepath):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Recording not found")
    
    return FileResponse(filepath, media_type="audio/wav")



@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "RAPID-100 Emergency Call Triage System"}


@app.post("/api/slm/process")
async def process_with_slm(request: dict):
    """Process text with the Small Language Model for emergency classification"""
    text = request.get("text", "")
    if not text:
        raise HTTPException(status_code=400, detail="Text is required")
    
    # Use SLM for classification
    result = slm.predict_call_details(text)
    
    # Map to our response format
    response = {
        "transcript": text,
        "emergency_type": result['emergency_type'],
        "severity": result['severity'],
        "background_noise": result['background_noise'],
        "voice_clarity": result['voice_clarity'],
        "emotion_intensity": result['emotion_intensity'],
        "features": result['features'],
        "confidence": 0.9  # Placeholder for now
    }
    
    return response


@app.get("/api/audio/filters")
async def get_audio_filters():
    """Get available audio filters for noise reduction"""
    from slm_emergency_classifier import create_audio_filters
    filters = create_audio_filters()
    return {"filters": filters}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)