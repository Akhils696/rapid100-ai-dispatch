import asyncio
import numpy as np
import soundfile as sf
import io
import logging
from typing import Optional
import tempfile
import os

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    print("Warning: whisper is not installed. Using mock transcription.")

logger = logging.getLogger(__name__)


class TranscriptionService:
    def __init__(self):
        self.model = None
        if WHISPER_AVAILABLE:
            try:
                self.model = whisper.load_model("tiny")
                logger.info("Whisper model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load Whisper model: {e}")
                self.model = None
        else:
            logger.warning("Whisper not available, using mock transcription")
        
        # Predefined responses for mock mode
        self.mock_responses = [
            "Help! My wife is unconscious and not breathing. She collapsed suddenly.",
            "There's a fire at my house! Smoke is everywhere, flames coming from the kitchen.",
            "Someone is breaking into my house! I hear glass breaking and footsteps.",
            "Car accident on Highway 101 near Exit 15. Multiple cars involved, people injured.",
            "Tornado warning! Severe weather approaching downtown. Taking shelter in basement."
        ]
        self.response_index = 0

    async def process_audio_chunk(self, audio_data: bytes) -> str:
        """
        Process an audio chunk and return the transcription
        In a real implementation, this would accumulate audio chunks and periodically transcribe
        """
        if self.model is not None:
            try:
                # Save audio data to temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
                    temp_file.write(audio_data)
                    temp_filename = temp_file.name
                
                # Load audio and transcribe
                result = self.model.transcribe(temp_filename)
                
                # Clean up temporary file
                os.unlink(temp_filename)
                
                return result['text'].strip()
            except Exception as e:
                logger.error(f"Error transcribing audio: {e}")
                return ""
        else:
            # Mock transcription service for development
            response = self.mock_responses[self.response_index % len(self.mock_responses)]
            self.response_index += 1
            await asyncio.sleep(0.1)  # Simulate processing time
            return response

    def preprocess_audio(self, audio_data: bytes) -> bytes:
        """
        Apply noise reduction and preprocessing to improve transcription quality
        """
        try:
            # Convert bytes to numpy array
            audio_buffer = io.BytesIO(audio_data)
            audio_array, sample_rate = sf.read(audio_buffer)
            
            # Apply basic noise reduction (simplified version)
            # In a real implementation, you would use more sophisticated techniques
            if len(audio_array.shape) > 1:
                audio_array = audio_array.mean(axis=1)  # Convert to mono if stereo
            
            # Normalize audio
            max_val = np.max(np.abs(audio_array))
            if max_val > 0:
                audio_array = audio_array / max_val
            
            # Write back to bytes
            processed_buffer = io.BytesIO()
            sf.write(processed_buffer, audio_array, sample_rate, format='WAV')
            
            return processed_buffer.getvalue()
        except Exception as e:
            logger.error(f"Error preprocessing audio: {e}")
            return audio_data  # Return original if preprocessing fails