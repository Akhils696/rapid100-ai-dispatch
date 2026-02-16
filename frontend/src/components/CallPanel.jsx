import React from 'react';

const CallPanel = ({ callData }) => {
  // Calculate emotion meter value based on keywords in transcript
  const calculateEmotionMeter = (transcript) => {
    if (!transcript) return 0;
    
    const urgentWords = ['help', 'emergency', 'urgent', 'immediately', 'now', 'quickly', 'hurry'];
    const emotionalWords = ['scared', 'afraid', 'hurt', 'pain', 'bleeding', 'unconscious', 'screaming', 'crying'];
    const distressWords = ['please', 'god', 'help me', 'save me', 'dying', 'dead'];
    
    const textLower = transcript.toLowerCase();
    let score = 0;
    
    urgentWords.forEach(word => {
      if (textLower.includes(word)) score += 1;
    });
    
    emotionalWords.forEach(word => {
      if (textLower.includes(word)) score += 1.5;
    });
    
    distressWords.forEach(word => {
      if (textLower.includes(word)) score += 2;
    });
    
    return Math.min(score / 6, 1); // Normalize to 0-1 range
  };

  // Calculate noise confidence based on transcript quality
  const calculateNoiseConfidence = (transcript) => {
    if (!transcript) return 0;
    
    // Simple heuristic: shorter transcripts might indicate poor audio
    const lengthScore = Math.min(transcript.length / 200, 1);
    
    // Check for common transcription artifacts that might indicate noise
    const noisyPatterns = ['you okay', 'can you hear me', 'hello', 'um', 'uh', 'ah'];
    let noiseScore = 0;
    
    const words = transcript.toLowerCase().split(/\s+/);
    noisyPatterns.forEach(pattern => {
      words.forEach(word => {
        if (word.includes(pattern)) noiseScore += 0.1;
      });
    });
    
    return Math.max(lengthScore - noiseScore, 0.1);
  };

  const emotionMeter = callData ? calculateEmotionMeter(callData.input_text || callData.transcript) : 0;
  const noiseConfidence = callData ? calculateNoiseConfidence(callData.input_text || callData.transcript) : 0;
  
  // Enhanced audio metrics from call data
  const audioMetrics = callData?.audio_metrics || {};
  const audioLevel = audioMetrics.level || 0;
  const qualityScore = audioMetrics.quality_score || noiseConfidence;
  const detectedLanguage = callData?.language || 'en';
  
  // Language display mapping
  const languageMap = {
    'en': 'English',
    'es': 'Spanish',
    'fr': 'French',
    'de': 'German',
    'hi': 'Hindi',
    'zh': 'Chinese',
    'ja': 'Japanese',
    'ar': 'Arabic'
  };
  
  const languageDisplay = languageMap[detectedLanguage] || 'Unknown';

  // Determine severity color
  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'CRITICAL': return 'bg-red-500';
      case 'HIGH': return 'bg-orange-500';
      case 'MEDIUM': return 'bg-yellow-500';
      case 'LOW': return 'bg-green-500';
      default: return 'bg-gray-500';
    }
  };

  return (
    <div className="bg-gray-800 rounded-lg shadow-lg h-full">
      <div className="p-4 border-b border-gray-700">
        <h2 className="text-lg font-semibold text-white flex items-center">
          <span className="w-3 h-3 bg-emergency-red rounded-full mr-2 animate-pulse"></span>
          Live Call Panel
        </h2>
      </div>
      
      <div className="p-4">
        {callData ? (
          <div className="space-y-4">
            {/* Real-time Transcript */}
            <div>
              <div className="flex justify-between items-center mb-2">
                <h3 className="text-sm font-medium text-gray-300">Real-time Transcript</h3>
                {detectedLanguage && (
                  <span className="text-xs bg-blue-900 text-blue-200 px-2 py-1 rounded">
                    {languageDisplay}
                  </span>
                )}
              </div>
              <div className="bg-gray-900 rounded p-3 max-h-32 overflow-y-auto border border-gray-700">
                <p className="text-emergency-green text-sm font-mono leading-relaxed">
                  {callData.input_text || callData.transcript || 'No transcript available'}
                </p>
              </div>
            </div>

            {/* Emotion Meter */}
            <div>
              <div className="flex justify-between items-center mb-1">
                <h3 className="text-sm font-medium text-gray-300">Emotion Intensity</h3>
                <span className="text-xs text-gray-400">{Math.round(emotionMeter * 100)}%</span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-2">
                <div 
                  className="bg-gradient-to-r from-yellow-500 to-red-500 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${emotionMeter * 100}%` }}
                ></div>
              </div>
            </div>

            {/* Enhanced Audio Quality Metrics */}
            <div className="space-y-3">
              <div>
                <div className="flex justify-between items-center mb-1">
                  <h3 className="text-sm font-medium text-gray-300">Audio Quality</h3>
                  <span className="text-xs text-gray-400">{Math.round(qualityScore * 100)}%</span>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-2">
                  <div 
                    className={`h-2 rounded-full transition-all duration-300 ${
                      qualityScore > 0.7 ? 'bg-green-500' : 
                      qualityScore > 0.4 ? 'bg-yellow-500' : 'bg-red-500'
                    }`}
                    style={{ width: `${qualityScore * 100}%` }}
                  ></div>
                </div>
              </div>
              
              {/* Audio Level Visualization */}
              <div>
                <div className="flex justify-between items-center mb-1">
                  <h3 className="text-sm font-medium text-gray-300">Audio Level</h3>
                  <span className="text-xs text-gray-400">{Math.round(audioLevel * 100)}%</span>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-2">
                  <div 
                    className={`h-2 rounded-full transition-all duration-150 ${
                      audioLevel > 0.8 ? 'bg-red-500' : 
                      audioLevel > 0.2 ? 'bg-green-500' : 'bg-yellow-500'
                    }`}
                    style={{ width: `${Math.min(audioLevel * 100, 100)}%` }}
                  ></div>
                </div>
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>Too Quiet</span>
                  <span>Optimal</span>
                  <span>Too Loud</span>
                </div>
              </div>
            </div>

            {/* Severity Badge */}
            <div>
              <h3 className="text-sm font-medium text-gray-300 mb-1">Severity Level</h3>
              <span className={`${getSeverityColor(callData.severity)} text-white text-xs px-2 py-1 rounded-full`}>
                {callData.severity}
              </span>
            </div>
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            <p>No active call</p>
            <p className="text-sm mt-2">Click a scenario to simulate an emergency call</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default CallPanel;