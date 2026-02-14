"""
Small Language Model (SLM) for Emergency Call Classification
This lightweight model is designed specifically for emergency call processing
"""
import pandas as pd
import numpy as np
import pickle
import json
import re
from typing import Dict, List, Tuple, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import joblib
import os


class EmergencyCallSLM:
    """
    Small Language Model designed specifically for emergency call classification
    """
    def __init__(self):
        self.emergency_types = ['FIRE', 'MEDICAL', 'CRIME', 'ACCIDENT', 'DISASTER', 'UNKNOWN']
        self.severity_levels = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']
        
        # Define keyword dictionaries for each emergency type
        self.type_keywords = {
            'MEDICAL': [
                'unconscious', 'breathing', 'bleeding', 'heart attack', 'stroke', 'pain', 
                'injury', 'ambulance', 'sick', 'ill', 'medicine', 'doctor', 'hospital',
                'medication', 'prescription', 'symptom', 'fever', 'broken bone', 'burn',
                'choke', 'cough', 'wheeze', 'allergic', 'overdose', 'seizure', 'faint'
            ],
            'FIRE': [
                'fire', 'smoke', 'burning', 'flames', 'burn', 'explode', 'gas leak',
                'explosion', 'blaze', 'inferno', 'combustion', 'ignite', 'torch',
                'burning smell', 'smoke detector', 'house fire', 'kitchen fire'
            ],
            'CRIME': [
                'gun', 'shot', 'robbery', 'steal', 'break in', 'burglary', 'assault',
                'murder', 'rape', 'kidnap', 'threat', 'dangerous', 'criminal', 'police',
                'arrest', 'homicide', 'weapon', 'stab', 'fight', 'violence', 'domestic',
                'screaming', 'shots fired', 'breaking glass', 'sirens'
            ],
            'ACCIDENT': [
                'accident', 'crash', 'collision', 'car', 'truck', 'vehicle', 'hit',
                'injured', 'wreck', 'fender bender', 'rollover', 'pedestrian', 'bike',
                'motorcycle', 'pileup', 'multi-car', 'intersection', 'collided'
            ],
            'DISASTER': [
                'tornado', 'hurricane', 'earthquake', 'flood', 'tsunami', 'avalanche',
                'landslide', 'wildfire', 'storm', 'emergency', 'evacuation', 'shelter',
                'weather', 'severe', 'disaster', 'catastrophe', 'natural disaster',
                'explosion', 'strong winds', 'trees falling', 'roof damaged'
            ]
        }
        
        # Define severity keywords
        self.severity_keywords = {
            'CRITICAL': [
                'unconscious', 'not breathing', 'heart attack', 'stroke', 'bleeding heavily',
                'severe bleeding', 'cardiac arrest', 'choking', 'drowning', 'electrocution',
                'severe burn', 'multiple injuries', 'life-threatening', 'critical condition',
                'immediate danger', 'active shooter', 'explosion imminent', 'mass casualty',
                'barely conscious', 'weak voice', 'can\'t breathe', 'choking', 'oh god help'
            ],
            'HIGH': [
                'injured', 'pain', 'broken bone', 'burn', 'accident', 'crash', 'fire',
                'smoke', 'gunshot', 'stabbed', 'assault', 'robbery', 'dangerous',
                'urgent', 'emergency', 'serious', 'major', 'significant', 'many injured',
                'multiple shots', 'severe pain', 'bleeding', 'difficulty breathing'
            ],
            'MEDIUM': [
                'sick', 'ill', 'fever', 'minor injury', 'small fire', 'property damage',
                'disturbance', 'noise complaint', 'lost', 'stranded', 'locked out',
                'medical concern', 'first aid needed', 'property crime', 'moderate pain',
                'possible overdose', 'neck pain', 'fell'
            ],
            'LOW': [
                'inquiry', 'information', 'non-urgent', 'routine', 'follow-up',
                'administrative', 'scheduled', 'appointment', 'general question',
                'power outage', 'tree down', 'dog bite', 'fender-bender'
            ]
        }
        
        # Initialize vectorizer and classifier
        self.vectorizer = TfidfVectorizer(max_features=5000, stop_words='english', ngram_range=(1, 2))
        self.classifier = LogisticRegression(random_state=42, max_iter=1000)
        
        # Background noise classification patterns
        self.noise_patterns = {
            'Low': [
                r'silence', r'quiet', r'clear voice', r'no background', r'low noise'
            ],
            'Medium': [
                r'medium noise', r'background noise', r'slight disturbance', 
                r'normal household sounds', r'cars passing'
            ],
            'High': [
                r'loud', r'screaming', r'shouting', r'sirens', r'glass breaking',
                r'explosion', r'fireworks', r'construction', r'heavy traffic',
                r'party', r'music', r'crowd', r'arguments'
            ],
            'Very High': [
                r'extremely loud', r'chaos', r'multiple voices', r'sounds of crash',
                r'explosion sounds', r'continuous screaming', r'loud bangs'
            ]
        }
        
        self.trained = False

    def extract_features(self, text: str) -> Dict[str, float]:
        """
        Extract features from text for classification
        """
        features = {}
        
        # Keyword matching for each type
        for emergency_type, keywords in self.type_keywords.items():
            count = sum(1 for keyword in keywords if keyword.lower() in text.lower())
            features[f'{emergency_type}_keywords'] = count
        
        # Keyword matching for severity
        for severity, keywords in self.severity_keywords.items():
            count = sum(1 for keyword in keywords if keyword.lower() in text.lower())
            features[f'{severity}_keywords'] = count
        
        # Text statistics
        features['text_length'] = len(text)
        features['word_count'] = len(text.split())
        features['exclamation_count'] = text.count('!')
        features['question_count'] = text.count('?')
        features['caps_ratio'] = sum(1 for c in text if c.isupper()) / max(len(text), 1)
        
        # Emotional indicators
        urgent_words = ['help', 'emergency', 'urgent', 'immediately', 'now', 'quickly', 'please']
        emotional_words = ['scared', 'afraid', 'hurt', 'pain', 'bleeding', 'unconscious', 'oh god', 'god']
        
        features['urgent_word_count'] = sum(1 for word in urgent_words if word in text.lower())
        features['emotional_word_count'] = sum(1 for word in emotional_words if word in text.lower())
        
        return features

    def classify_emergency_type(self, text: str) -> str:
        """
        Classify the type of emergency based on text
        """
        if self.trained:
            # Use the trained model if available
            text_vector = self.vectorizer.transform([text])
            prediction = self.classifier.predict(text_vector)[0]
            return prediction
        else:
            # Use rule-based classification if not trained
            scores = {}
            for emergency_type, keywords in self.type_keywords.items():
                scores[emergency_type] = sum(1 for keyword in keywords if keyword.lower() in text.lower())
            
            # If no keywords match, return UNKNOWN
            if max(scores.values()) == 0:
                return 'UNKNOWN'
            
            return max(scores, key=scores.get)

    def classify_severity(self, text: str) -> str:
        """
        Classify the severity level based on text
        """
        scores = {}
        for severity, keywords in self.severity_keywords.items():
            scores[severity] = sum(1 for keyword in keywords if keyword.lower() in text.lower())
        
        # If no keywords match, default to MEDIUM
        if max(scores.values()) == 0:
            return 'MEDIUM'
        
        return max(scores, key=scores.get)

    def classify_background_noise(self, text: str) -> str:
        """
        Classify the level of background noise
        """
        # This is a simplified approach - in a real system, you'd analyze audio features
        # Here we'll infer from descriptive text in the call
        text_lower = text.lower()
        
        # Check for noise indicators
        high_noise_indicators = ['screaming', 'shouting', 'sirens', 'glass breaking', 'explosion', 'bangs', 'chaos']
        medium_noise_indicators = ['background', 'noise', 'crowd', 'music', 'traffic', 'sounds']
        
        high_count = sum(1 for indicator in high_noise_indicators if indicator in text_lower)
        medium_count = sum(1 for indicator in medium_noise_indicators if indicator in text_lower)
        
        if high_count >= 2:
            return 'Very High'
        elif high_count >= 1:
            return 'High'
        elif medium_count >= 1:
            return 'Medium'
        else:
            return 'Low'

    def estimate_voice_clarity(self, text: str) -> str:
        """
        Estimate voice clarity based on text characteristics
        """
        # In a real system, this would analyze audio quality metrics
        # Here we'll infer from text quality
        if len(text.strip()) < 10:
            return 'Unclear'  # Very short, possibly unclear
        
        # Look for signs of unclear speech
        unclear_indicators = ['...', 'um', 'uh', 'hmm', 'not sure', 'maybe', 'possibly']
        unclear_count = sum(1 for indicator in unclear_indicators if indicator in text.lower())
        
        if unclear_count >= 3:
            return 'Unclear'
        else:
            return 'Clear'

    def estimate_emotion_intensity(self, text: str) -> float:
        """
        Estimate emotion intensity from text (0.0 to 1.0)
        """
        # Calculate emotion intensity based on various factors
        text_lower = text.lower()
        
        # Emotional keywords
        emotional_keywords = [
            'help', 'emergency', 'urgent', 'immediately', 'now', 'quickly', 'please',
            'scared', 'afraid', 'hurt', 'pain', 'bleeding', 'unconscious', 'oh god', 'god',
            'choking', 'can\'t breathe', 'dying', 'die', 'worst', 'terrible', 'horrible'
        ]
        
        emotion_score = sum(1 for word in emotional_keywords if word in text_lower)
        
        # Exclamation marks contribute to emotion
        exclamation_score = text.count('!') * 0.2
        
        # Caps ratio contributes to emotion
        caps_score = (sum(1 for c in text if c.isupper()) / max(len(text), 1)) * 0.3
        
        # Combine scores and normalize to 0-1 range
        total_score = min((emotion_score * 0.1 + exclamation_score + caps_score), 1.0)
        
        return max(total_score, 0.1)  # Minimum emotion level

    def train(self, dataset_path: str = None, df: pd.DataFrame = None):
        """
        Train the SLM on emergency call data
        """
        if df is None:
            if dataset_path is None:
                dataset_path = "dataset/emergency_calls_dataset.csv"
            df = pd.read_csv(dataset_path)
        
        # Prepare training data
        X_text = df['transcript'].fillna('').astype(str)
        y_type = df['emergency_type']
        
        # Vectorize the text
        X_vectorized = self.vectorizer.fit_transform(X_text)
        
        # Train the classifier
        self.classifier.fit(X_vectorized, y_type)
        
        self.trained = True
        print("SLM trained successfully!")

    def predict_call_details(self, text: str) -> Dict:
        """
        Predict all call details: type, severity, background noise, etc.
        """
        return {
            'emergency_type': self.classify_emergency_type(text),
            'severity': self.classify_severity(text),
            'background_noise': self.classify_background_noise(text),
            'voice_clarity': self.estimate_voice_clarity(text),
            'emotion_intensity': self.estimate_emotion_intensity(text),
            'features': self.extract_features(text)
        }

    def save_model(self, filepath: str):
        """
        Save the trained model
        """
        model_data = {
            'vectorizer': self.vectorizer,
            'classifier': self.classifier,
            'trained': self.trained
        }
        joblib.dump(model_data, filepath)
        print(f"Model saved to {filepath}")

    def load_model(self, filepath: str):
        """
        Load a trained model
        """
        model_data = joblib.load(filepath)
        self.vectorizer = model_data['vectorizer']
        self.classifier = model_data['classifier']
        self.trained = model_data['trained']
        print(f"Model loaded from {filepath}")


def create_audio_filters():
    """
    Create audio filters for noise reduction and voice enhancement
    """
    # This function would typically interface with audio processing libraries
    # For this SLM implementation, we'll return filter parameters
    filters = {
        'noise_reduction': {
            'enabled': True,
            'threshold_db': -30,
            'frequency_range': (20, 20000),  # Hz
            'algorithm': 'spectral_subtraction'
        },
        'voice_enhancement': {
            'enabled': True,
            'gain_db': 3,
            'frequency_boost': 1000,  # Hz
            'algorithm': 'dynamic_range_compression'
        },
        'background_isolation': {
            'enabled': True,
            'frequency_threshold': 500,  # Hz (separate low freq background from voice)
            'algorithm': 'spectral_masking'
        }
    }
    return filters


def extract_background_noises(audio_data):
    """
    Extract background noises from audio data
    """
    # In a real implementation, this would process the audio signal
    # For now, return a placeholder with common background noises
    background_noises = [
        "ambient room tone",
        "air conditioning hum",
        "traffic noise",
        "people talking in background",
        "TV or radio playing",
        "construction noise",
        "sirens in distance"
    ]
    return background_noises


def main():
    """
    Main function to demonstrate the SLM
    """
    print("Initializing Emergency Call SLM...")
    slm = EmergencyCallSLM()
    
    # Train the model
    print("Training the model...")
    try:
        slm.train()
    except FileNotFoundError:
        print("Dataset file not found. Using rule-based classification.")
    
    # Example emergency calls
    test_calls = [
        "Help! My wife is unconscious and not breathing. She collapsed suddenly. Please send an ambulance immediately!",
        "There's a fire at my house! Smoke is everywhere, flames coming from the kitchen. Need firefighters now!",
        "Someone is breaking into my house! I hear glass breaking and footsteps. Gunshots fired. Police needed immediately!",
        "Car accident on Highway 101 near Exit 15. Multiple cars involved, people injured. Need ambulances and police.",
        "Tornado warning! Severe weather approaching downtown. Taking shelter in basement. Large debris flying."
    ]
    
    print("\nTesting the SLM on sample calls:")
    for i, call in enumerate(test_calls, 1):
        print(f"\nCall {i}: {call[:50]}...")
        result = slm.predict_call_details(call)
        print(f"  Emergency Type: {result['emergency_type']}")
        print(f"  Severity: {result['severity']}")
        print(f"  Background Noise: {result['background_noise']}")
        print(f"  Voice Clarity: {result['voice_clarity']}")
        print(f"  Emotion Intensity: {result['emotion_intensity']:.2f}")
    
    # Create audio filters
    print("\nCreating audio filters...")
    filters = create_audio_filters()
    for filter_type, params in filters.items():
        print(f"  {filter_type}: {params}")
    
    print("\nSLM initialization complete!")


if __name__ == "__main__":
    main()