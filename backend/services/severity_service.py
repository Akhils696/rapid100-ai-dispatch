import re
import logging
from typing import Dict
from collections import Counter

from models.call_data import SeverityLevel

logger = logging.getLogger(__name__)


class SeverityService:
    def __init__(self):
        # Define keywords that indicate different severity levels
        self.severity_keywords = {
            SeverityLevel.CRITICAL: [
                'unconscious', 'not breathing', 'heart attack', 'stroke', 'bleeding heavily',
                'severe bleeding', 'cardiac arrest', 'choking', 'drowning', 'electrocution',
                'severe burn', 'multiple injuries', 'life-threatening', 'critical condition',
                'immediate danger', 'active shooter', 'explosion imminent', 'mass casualty'
            ],
            SeverityLevel.HIGH: [
                'injured', 'pain', 'broken bone', 'burn', 'accident', 'crash', 'fire',
                'smoke', 'gunshot', 'stabbed', 'assault', 'robbery', 'dangerous',
                'urgent', 'emergency', 'serious', 'major', 'significant'
            ],
            SeverityLevel.MEDIUM: [
                'sick', 'ill', 'fever', 'minor injury', 'small fire', 'property damage',
                'disturbance', 'noise complaint', 'lost', 'stranded', 'locked out',
                'medical concern', 'first aid needed', 'property crime'
            ],
            SeverityLevel.LOW: [
                'inquiry', 'information', 'non-urgent', 'routine', 'follow-up',
                'administrative', 'scheduled', 'appointment', 'general question'
            ]
        }
        
        # Emotion/intensity indicators
        self.emotion_indicators = {
            'urgency': ['immediately', 'now', 'right away', 'hurry', 'quickly', 'fast'],
            'intensity': ['very', 'extremely', 'terribly', 'incredibly', 'highly'],
            'distress': ['help', 'please', 'oh god', 'oh no', 'scared', 'afraid']
        }

    def calculate_severity(self, text: str) -> SeverityLevel:
        """
        Calculate the severity level based on keywords and emotional indicators
        """
        text_lower = text.lower()
        
        # Score each severity level based on keyword matches
        severity_scores = {
            SeverityLevel.CRITICAL: 0,
            SeverityLevel.HIGH: 0,
            SeverityLevel.MEDIUM: 0,
            SeverityLevel.LOW: 0
        }
        
        # Count critical keywords (these take precedence)
        for keyword in self.severity_keywords[SeverityLevel.CRITICAL]:
            if keyword in text_lower:
                severity_scores[SeverityLevel.CRITICAL] += 2  # Higher weight for critical
        
        # Count other keywords
        for severity_level, keywords in self.severity_keywords.items():
            if severity_level != SeverityLevel.CRITICAL:
                for keyword in keywords:
                    if keyword in text_lower:
                        severity_scores[severity_level] += 1
        
        # Add bonus for emotional/intensity indicators
        for category, indicators in self.emotion_indicators.items():
            for indicator in indicators:
                if indicator in text_lower:
                    # Boost critical and high severity scores
                    severity_scores[SeverityLevel.CRITICAL] += 0.5
                    severity_scores[SeverityLevel.HIGH] += 0.5
        
        # Determine the highest scoring severity level
        max_severity = max(severity_scores, key=severity_scores.get)
        
        # If no keywords matched, default to medium
        if severity_scores[max_severity] == 0:
            return SeverityLevel.MEDIUM
        
        return max_severity

    def get_severity_confidence(self, text: str) -> Dict[SeverityLevel, float]:
        """
        Calculate confidence scores for each severity level
        """
        text_lower = text.lower()
        total_score = 0
        scores = {
            SeverityLevel.CRITICAL: 0,
            SeverityLevel.HIGH: 0,
            SeverityLevel.MEDIUM: 0,
            SeverityLevel.LOW: 0
        }
        
        # Calculate scores with weights
        for severity_level, keywords in self.severity_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    # Critical keywords get higher weight
                    weight = 2 if severity_level == SeverityLevel.CRITICAL else 1
                    scores[severity_level] += weight
                    total_score += weight
        
        # Add emotional indicators
        for category, indicators in self.emotion_indicators.items():
            for indicator in indicators:
                if indicator in text_lower:
                    # Distribute boost to critical and high
                    scores[SeverityLevel.CRITICAL] += 0.5
                    scores[SeverityLevel.HIGH] += 0.5
                    total_score += 1
        
        # Normalize scores
        if total_score > 0:
            for severity_level in scores:
                scores[severity_level] = min(scores[severity_level] / total_score, 1.0)
        else:
            # Default distribution if no keywords match
            scores[SeverityLevel.MEDIUM] = 0.8
            scores[SeverityLevel.LOW] = 0.2
        
        return scores

    def analyze_emotional_intensity(self, text: str) -> float:
        """
        Analyze the emotional intensity of the text (0.0 to 1.0)
        """
        text_lower = text.lower()
        intensity_score = 0
        
        # Count emotional indicators
        for category, indicators in self.emotion_indicators.items():
            for indicator in indicators:
                if indicator in text_lower:
                    intensity_score += 1
        
        # Normalize to 0-1 scale (assuming max possible indicators is 10)
        max_possible = sum(len(indicators) for indicators in self.emotion_indicators.values())
        if max_possible > 0:
            return min(intensity_score / max_possible, 1.0)
        else:
            return 0.0