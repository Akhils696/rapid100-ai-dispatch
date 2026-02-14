import re
import logging
from typing import Dict, List, Optional
import spacy
from transformers import pipeline

logger = logging.getLogger(__name__)


class LocationService:
    def __init__(self):
        # Try to load spaCy NER model
        try:
            self.nlp = spacy.load("en_core_web_sm")
            self.use_spacy = True
        except OSError:
            logger.warning("spaCy 'en_core_web_sm' model not found. Using regex-based location extraction.")
            self.use_spacy = False
            self.nlp = None
        
        # Regex patterns for location extraction
        self.address_patterns = [
            r'\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|Place|Pl)\.?',  # Street addresses
            r'[A-Z][a-z]+\s+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|Place|Pl)',  # Proper name streets
            r'(?:Downtown|Uptown|Midtown|City Center|Central Business District|CBD)',  # City areas
            r'[A-Z][a-z]+\s+(?:Park|Square|Mall|Center|Plaza|Hospital|School|University|Airport|Station)',  # Landmarks
            r'[A-Z][a-z]+,\s*[A-Z]{2}(?:\s+\d{5})?',  # City, State format
        ]
        
        # Common landmark types to look for
        self.landmark_keywords = [
            'hospital', 'school', 'university', 'airport', 'station', 'mall', 'park', 
            'hotel', 'restaurant', 'bank', 'store', 'center', 'square', 'plaza'
        ]

    def extract_location(self, text: str) -> str:
        """
        Extract location information from text using NER or regex patterns
        """
        if self.use_spacy:
            return self._extract_with_spacy(text)
        else:
            return self._extract_with_regex(text)

    def _extract_with_spacy(self, text: str) -> str:
        """
        Extract locations using spaCy NER
        """
        doc = self.nlp(text)
        locations = []
        
        for ent in doc.ents:
            if ent.label_ in ["GPE", "LOC", "FAC"]:  # Geopolitical entities, locations, facilities
                locations.append(ent.text)
        
        # Also look for address patterns
        for pattern in self.address_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if match not in locations:
                    locations.append(match)
        
        return ", ".join(locations) if locations else "Location not specified"

    def _extract_with_regex(self, text: str) -> str:
        """
        Extract locations using regex patterns
        """
        locations = []
        
        # Check for address patterns
        for pattern in self.address_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            locations.extend(matches)
        
        # Look for landmarks
        text_lower = text.lower()
        for keyword in self.landmark_keywords:
            # Find the landmark and surrounding context
            pattern = r'(?:\w+\s+)*\w*\s*' + re.escape(keyword) + r'\s*(?:\w+\s+)*(?:\w+)?'
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                # Capitalize properly
                formatted_match = ' '.join(word.capitalize() if i == 0 or word in ['hospital', 'school', 'university', 'airport', 'station', 'mall', 'park', 'hotel', 'restaurant', 'bank', 'store', 'center', 'square', 'plaza'] else word for i, word in enumerate(match.split()))
                if formatted_match not in locations:
                    locations.append(formatted_match)
        
        return ", ".join(locations) if locations else "Location not specified"

    def get_location_confidence(self, text: str) -> float:
        """
        Estimate confidence in location extraction (0.0 to 1.0)
        """
        location = self.extract_location(text)
        if location == "Location not specified":
            return 0.0
        
        # Simple heuristic: longer location extractions are more likely to be accurate
        # But cap at 0.9 to account for potential errors
        confidence = min(len(location) / 50.0, 0.9)
        return max(confidence, 0.3)  # Minimum confidence of 0.3 if location was found

    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extract various named entities from the text
        """
        entities = {
            "locations": [],
            "persons": [],
            "organizations": [],
            "misc": []
        }
        
        if self.use_spacy:
            doc = self.nlp(text)
            for ent in doc.ents:
                if ent.label_ in ["GPE", "LOC", "FAC"]:
                    entities["locations"].append(ent.text)
                elif ent.label_ == "PERSON":
                    entities["persons"].append(ent.text)
                elif ent.label_ in ["ORG", "NORP"]:  # Organizations, nationalities/religious/political groups
                    entities["organizations"].append(ent.text)
                else:
                    entities["misc"].append(f"{ent.text} ({ent.label_})")
        else:
            # Fallback: just extract locations using regex
            location = self.extract_location(text)
            if location != "Location not specified":
                entities["locations"].append(location)
        
        return entities