import re
import logging
from typing import List, Dict
from models.call_data import EmergencyType, SeverityLevel

logger = logging.getLogger(__name__)


class ExplanationService:
    def __init__(self):
        # Keywords that trigger specific explanations
        self.emergency_explanation_keywords = {
            EmergencyType.MEDICAL: [
                ('unconscious', 'Person is not responsive, indicating a serious medical emergency'),
                ('breathing', 'Breathing difficulty suggests immediate medical attention needed'),
                ('heart attack', 'Classic sign of cardiac emergency requiring urgent care'),
                ('stroke', 'Neurological emergency requiring immediate medical intervention'),
                ('bleeding', 'Significant blood loss requires prompt medical attention'),
                ('pain', 'Severe pain may indicate serious underlying condition')
            ],
            EmergencyType.FIRE: [
                ('fire', 'Active fire poses immediate danger to life and property'),
                ('smoke', 'Smoke inhalation is deadly, evacuation needed immediately'),
                ('burning', 'Combustible materials are ignited, spreading risk'),
                ('flames', 'Visible flames indicate active fire requiring suppression')
            ],
            EmergencyType.CRIME: [
                ('gun', 'Firearm present creates extreme danger to all parties'),
                ('shot', 'Gunshot wounds are life-threatening and require immediate response'),
                ('robbery', 'Criminal act in progress with potential for violence'),
                ('break in', 'Unauthorized entry indicates security breach and potential threat'),
                ('assault', 'Physical attack occurring requiring law enforcement'),
                ('dangerous', 'Situation presents risk to public safety')
            ],
            EmergencyType.ACCIDENT: [
                ('accident', 'Traffic incident with potential for injuries and hazards'),
                ('crash', 'Vehicle collision likely caused injuries and road hazards'),
                ('collision', 'Impact event that may have caused trauma to individuals'),
                ('injured', 'People harmed requiring medical attention'),
                ('wreck', 'Severe vehicle damage suggesting significant impact')
            ],
            EmergencyType.DISASTER: [
                ('tornado', 'Severe weather event causing widespread destruction'),
                ('hurricane', 'Major storm system creating emergency conditions'),
                ('earthquake', 'Ground shaking causing structural damage and hazards'),
                ('flood', 'Water overflow creating dangerous conditions'),
                ('emergency', 'Declared state of emergency requiring coordinated response')
            ]
        }
        
        # Severity explanation keywords
        self.severity_explanation_keywords = {
            SeverityLevel.CRITICAL: [
                ('unconscious', 'Victim unresponsive, immediate life threat'),
                ('not breathing', 'Respiratory failure, minutes matter'),
                ('heart attack', 'Cardiac arrest, time-sensitive intervention'),
                ('stroke', 'Brain function compromised, urgent treatment needed'),
                ('bleeding heavily', 'Rapid blood loss, shock risk'),
                ('life-threatening', 'Immediate danger to life')
            ],
            SeverityLevel.HIGH: [
                ('injured', 'Physical harm requiring medical attention'),
                ('pain', 'Discomfort indicating possible injury'),
                ('fire', 'Dangerous situation needing rapid response'),
                ('urgent', 'Time-sensitive but not immediately life-threatening'),
                ('serious', 'Substantial risk or harm present')
            ],
            SeverityLevel.MEDIUM: [
                ('sick', 'Illness requiring evaluation'),
                ('minor injury', 'Less severe harm but still needs attention'),
                ('medical concern', 'Health issue that should be checked'),
                ('property damage', 'Material loss but no immediate personal danger')
            ],
            SeverityLevel.LOW: [
                ('inquiry', 'Information request, non-emergency'),
                ('non-urgent', 'Can wait for routine handling'),
                ('routine', 'Standard procedure, no immediate action needed')
            ]
        }

    def generate_explanation(self, text: str, emergency_type: EmergencyType, severity: SeverityLevel) -> str:
        """
        Generate an explanation for why the classification and severity were assigned
        """
        text_lower = text.lower()
        explanations = []
        
        # Add emergency type explanation
        type_explanations = self._find_matching_explanations(
            text_lower, 
            self.emergency_explanation_keywords.get(emergency_type, []), 
            "emergency type"
        )
        explanations.extend(type_explanations)
        
        # Add severity explanation
        severity_explanations = self._find_matching_explanations(
            text_lower, 
            self.severity_explanation_keywords.get(severity, []), 
            "severity level"
        )
        explanations.extend(severity_explanations)
        
        # Add general explanation if no specific matches
        if not explanations:
            explanations.append(
                f"The system classified this as {emergency_type.value} with {severity.value} severity "
                f"based on analysis of the audio transcription and contextual cues."
            )
        
        # Combine explanations
        return " ".join(explanations)

    def _find_matching_explanations(self, text_lower: str, keyword_explanations: List[tuple], category: str) -> List[str]:
        """
        Find matching keywords in text and return corresponding explanations
        """
        explanations = []
        
        for keyword, explanation in keyword_explanations:
            if keyword in text_lower:
                explanations.append(explanation)
        
        # If no specific explanations found, provide a general one
        if not explanations and keyword_explanations:
            keyword_list = [kw[0] for kw in keyword_explanations[:3]]  # Take first 3 keywords as examples
            if keyword_list:
                explanations.append(
                    f"Keywords like '{', '.join(keyword_list)}' in the text led to this {category} determination."
                )
        
        return explanations

    def highlight_key_phrases(self, text: str, emergency_type: EmergencyType, severity: SeverityLevel) -> List[str]:
        """
        Identify and return key phrases that influenced the decision
        """
        text_lower = text.lower()
        key_phrases = []
        
        # Collect all relevant keywords for the determined type and severity
        relevant_keywords = []
        
        if emergency_type in self.emergency_explanation_keywords:
            relevant_keywords.extend([kw[0] for kw in self.emergency_explanation_keywords[emergency_type]])
        
        if severity in self.severity_explanation_keywords:
            relevant_keywords.extend([kw[0] for kw in self.severity_explanation_keywords[severity]])
        
        # Find occurrences of these keywords in the text
        for keyword in relevant_keywords:
            # Use word boundaries to match whole words/phrases
            pattern = r'\b' + re.escape(keyword) + r'\b'
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                # Get the sentence containing the keyword
                start = text.rfind('.', 0, match.start()) + 1
                end = text.find('.', match.end())
                if end == -1:
                    end = len(text)
                
                sentence = text[start:end].strip()
                if sentence and sentence not in key_phrases:
                    key_phrases.append(sentence)
        
        return key_phrases[:5]  # Return top 5 key phrases

    def generate_timeline_explanation(self, text: str, emergency_type: EmergencyType, severity: SeverityLevel) -> Dict[str, str]:
        """
        Generate a timeline-style explanation showing the decision process
        """
        timeline = {
            "speech": "Audio received from emergency caller",
            "transcript": f"'{text}' - Transcribed speech content",
            "classification": f"Detected {emergency_type.value} emergency based on key terms",
            "severity": f"Determined {severity.value} severity level",
            "routing": f"Suggested routing to appropriate emergency services"
        }
        
        return timeline