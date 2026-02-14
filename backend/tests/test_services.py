import pytest
import asyncio
from unittest.mock import Mock, patch
import numpy as np

from ..services.transcription_service import TranscriptionService
from ..services.classification_service import ClassificationService
from ..services.severity_service import SeverityService
from ..services.location_service import LocationService
from ..services.explanation_service import ExplanationService
from ..models.call_data import EmergencyType, SeverityLevel


class TestTranscriptionService:
    def setup_method(self):
        self.service = TranscriptionService()

    def test_process_audio_chunk_mock_mode(self):
        # Test that mock mode works when whisper is not available
        result = asyncio.run(self.service.process_audio_chunk(b"dummy audio data"))
        assert isinstance(result, str)
        assert len(result) > 0

    def test_preprocess_audio(self):
        # Test audio preprocessing function
        dummy_audio = b"dummy audio data"
        result = self.service.preprocess_audio(dummy_audio)
        assert isinstance(result, bytes)


class TestClassificationService:
    def setup_method(self):
        self.service = ClassificationService()

    @pytest.mark.parametrize("text,expected_type", [
        ("help my wife is unconscious", EmergencyType.MEDICAL),
        ("there is a fire in my house", EmergencyType.FIRE),
        ("someone is breaking into my home", EmergencyType.CRIME),
        ("car accident on highway", EmergencyType.ACCIDENT),
        ("tornado warning", EmergencyType.DISASTER),
        ("hello how are you", EmergencyType.UNKNOWN)
    ])
    def test_classify_emergency(self, text, expected_type):
        result = self.service.classify_emergency(text)
        assert result == expected_type

    def test_get_emergency_confidence(self):
        text = "help my wife is unconscious"
        result = self.service.get_emergency_confidence(text)
        
        assert isinstance(result, dict)
        assert all(isinstance(key, EmergencyType) for key in result.keys())
        assert all(0 <= value <= 1 for value in result.values())


class TestSeverityService:
    def setup_method(self):
        self.service = SeverityService()

    @pytest.mark.parametrize("text,expected_severity", [
        ("unconscious not breathing heart attack", SeverityLevel.CRITICAL),
        ("injured in accident broken leg", SeverityLevel.HIGH),
        ("sick with fever minor cut", SeverityLevel.MEDIUM),
        ("asking for information", SeverityLevel.LOW)
    ])
    def test_calculate_severity(self, text, expected_severity):
        result = self.service.calculate_severity(text)
        assert result == expected_severity

    def test_get_severity_confidence(self):
        text = "unconscious not breathing"
        result = self.service.get_severity_confidence(text)
        
        assert isinstance(result, dict)
        assert all(isinstance(key, SeverityLevel) for key in result.keys())
        assert all(0 <= value <= 1 for value in result.values())

    def test_analyze_emotional_intensity(self):
        text = "please help me now very scared"
        result = self.service.analyze_emotional_intensity(text)
        
        assert isinstance(result, float)
        assert 0 <= result <= 1


class TestLocationService:
    def setup_method(self):
        self.service = LocationService()

    @pytest.mark.parametrize("text,expected_contains", [
        ("at 123 Main St Downtown", "Main St"),
        ("near Central Hospital", "Hospital"),
        ("on Highway 101", "Highway"),
        ("downtown area", "downtown"),
        ("no location mentioned", "Location not specified")
    ])
    def test_extract_location(self, text, expected_contains):
        result = self.service.extract_location(text)
        assert expected_contains in result

    def test_get_location_confidence(self):
        text = "at 123 Main St Downtown"
        result = self.service.get_location_confidence(text)
        
        assert isinstance(result, float)
        assert 0 <= result <= 1

    def test_extract_entities(self):
        text = "Help at Central Hospital on Main Street"
        result = self.service.extract_entities(text)
        
        assert isinstance(result, dict)
        assert "locations" in result
        assert "persons" in result
        assert "organizations" in result
        assert "misc" in result


class TestExplanationService:
    def setup_method(self):
        self.service = ExplanationService()

    def test_generate_explanation(self):
        text = "help my wife is unconscious"
        result = self.service.generate_explanation(text, EmergencyType.MEDICAL, SeverityLevel.CRITICAL)
        
        assert isinstance(result, str)
        assert len(result) > 0

    def test_highlight_key_phrases(self):
        text = "help my wife is unconscious and not breathing"
        result = self.service.highlight_key_phrases(text, EmergencyType.MEDICAL, SeverityLevel.CRITICAL)
        
        assert isinstance(result, list)
        assert len(result) <= 5  # Max 5 phrases

    def test_generate_timeline_explanation(self):
        text = "emergency call for help"
        result = self.service.generate_timeline_explanation(text, EmergencyType.MEDICAL, SeverityLevel.HIGH)
        
        assert isinstance(result, dict)
        assert "speech" in result
        assert "transcript" in result
        assert "classification" in result
        assert "severity" in result
        assert "routing" in result