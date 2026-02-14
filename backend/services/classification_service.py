import re
import logging
from typing import Dict, List
import numpy as np
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from transformers import pipeline
import torch

from models.call_data import EmergencyType

logger = logging.getLogger(__name__)


class ClassificationService:
    def __init__(self):
        self.emergency_keywords = {
            EmergencyType.MEDICAL: [
                'unconscious', 'breathing', 'bleeding', 'heart attack', 'stroke', 'pain', 
                'injury', 'ambulance', 'sick', 'ill', 'medicine', 'doctor', 'hospital',
                'medication', 'prescription', 'symptom', 'fever', 'broken bone', 'burn'
            ],
            EmergencyType.FIRE: [
                'fire', 'smoke', 'burning', 'flames', 'burn', 'explode', 'gas leak',
                'explosion', 'blaze', 'inferno', 'combustion', 'ignite', 'torch'
            ],
            EmergencyType.CRIME: [
                'gun', 'shot', 'robbery', 'steal', 'break in', 'burglary', 'assault',
                'murder', 'rape', 'kidnap', 'threat', 'dangerous', 'criminal', 'police',
                'arrest', 'homicide', 'weapon', 'stab', 'fight', 'violence'
            ],
            EmergencyType.ACCIDENT: [
                'accident', 'crash', 'collision', 'car', 'truck', 'vehicle', 'hit',
                'injured', 'wreck', 'fender bender', 'rollover', 'pedestrian', 'bike',
                'motorcycle', 'pileup', 'multi-car'
            ],
            EmergencyType.DISASTER: [
                'tornado', 'hurricane', 'earthquake', 'flood', 'tsunami', 'avalanche',
                'landslide', 'wildfire', 'storm', 'emergency', 'evacuation', 'shelter',
                'weather', 'severe', 'disaster', 'catastrophe', 'natural disaster'
            ]
        }
        
        # Initialize transformer model (using a pre-trained model for classification)
        try:
            self.classifier = pipeline(
                "text-classification",
                model="distilbert-base-uncased-finetuned-sst-2-english",
                return_all_scores=True
            )
            self.use_transformer = True
        except Exception as e:
            logger.warning(f"Could not load transformer model: {e}. Using keyword-based classification.")
            self.use_transformer = False

    def classify_emergency(self, text: str) -> EmergencyType:
        """
        Classify the type of emergency based on the text
        Uses both keyword matching and transformer model if available
        """
        text_lower = text.lower()
        
        # Count keyword matches for each emergency type
        keyword_scores = {}
        for emergency_type, keywords in self.emergency_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            keyword_scores[emergency_type] = score
        
        # If transformer model is available, combine with keyword scores
        if self.use_transformer:
            # This is a simplified approach - in reality, you'd need a model trained specifically for emergency classification
            transformer_result = self.classifier(text[:512])  # Limit text length
            # For demonstration, we'll prioritize keyword matching but adjust with transformer confidence
            max_keyword_type = max(keyword_scores, key=keyword_scores.get)
            max_keyword_score = keyword_scores[max_keyword_type]
            
            if max_keyword_score > 0:
                return max_keyword_type
            else:
                # If no keywords matched, default to unknown
                return EmergencyType.UNKNOWN
        else:
            # Use only keyword matching
            max_type = max(keyword_scores, key=keyword_scores.get)
            if keyword_scores[max_type] > 0:
                return max_type
            else:
                return EmergencyType.UNKNOWN

    def get_emergency_confidence(self, text: str) -> Dict[EmergencyType, float]:
        """
        Calculate confidence scores for each emergency type
        """
        text_lower = text.lower()
        total_matches = 0
        scores = {}
        
        for emergency_type, keywords in self.emergency_keywords.items():
            count = sum(1 for keyword in keywords if keyword in text_lower)
            scores[emergency_type] = count
            total_matches += count
        
        # Normalize scores to 0-1 range
        if total_matches > 0:
            for emergency_type in scores:
                scores[emergency_type] = scores[emergency_type] / total_matches
        
        # Add small probability for unknown if no matches
        if total_matches == 0:
            for emergency_type in scores:
                scores[emergency_type] = 0.0
            scores[EmergencyType.UNKNOWN] = 1.0
        elif scores[EmergencyType.UNKNOWN] == 0:
            # Distribute some probability to unknown
            for emergency_type in scores:
                scores[emergency_type] *= 0.9
            scores[EmergencyType.UNKNOWN] = 0.1
        
        return scores