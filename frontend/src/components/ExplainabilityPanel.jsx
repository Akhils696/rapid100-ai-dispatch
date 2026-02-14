import React from 'react';

const ExplainabilityPanel = ({ callData }) => {
  // Highlight key phrases in the transcript
  const highlightKeyPhrases = (transcript, explanation) => {
    if (!transcript || !explanation) return transcript;
    
    // Simple approach: highlight common emergency keywords
    const emergencyKeywords = [
      'help', 'emergency', 'unconscious', 'breathing', 'bleeding', 'fire', 'smoke', 
      'gun', 'shot', 'accident', 'crash', 'pain', 'hurt', 'medical', 'ambulance',
      'police', 'fire department', 'accident', 'injury', 'injured', 'danger'
    ];
    
    let highlightedText = transcript;
    emergencyKeywords.forEach(keyword => {
      const regex = new RegExp(`(${keyword})`, 'gi');
      highlightedText = highlightedText.replace(regex, '<mark class="bg-yellow-300 text-black">$1</mark>');
    });
    
    return highlightedText;
  };

  // Generate explanation bullets based on classification
  const generateExplanationBullets = (callData) => {
    if (!callData) return [];
    
    const bullets = [];
    
    // Why this emergency type was selected
    if (callData.predicted_class === 'MEDICAL') {
      bullets.push('Detected medical terminology: words like "pain", "hurt", "bleeding", "unconscious"');
      bullets.push('Speech pattern suggests medical distress');
    } else if (callData.predicted_class === 'FIRE') {
      bullets.push('Detected fire-related terms: "fire", "smoke", "burning", "flames"');
      bullets.push('Urgent tone indicates immediate danger');
    } else if (callData.predicted_class === 'CRIME') {
      bullets.push('Detected criminal activity terms: "gun", "shot", "robbery", "break in"');
      bullets.push('Threatening language patterns identified');
    } else if (callData.predicted_class === 'ACCIDENT') {
      bullets.push('Detected accident-related terms: "crash", "accident", "hit", "wreck"');
      bullets.push('Context suggests traffic or collision incident');
    } else if (callData.predicted_class === 'DISASTER') {
      bullets.push('Detected disaster-related terms: "tornado", "hurricane", "flood", "emergency"');
      bullets.push('Environmental hazard indicators present');
    }
    
    // Why this severity was assigned
    if (callData.severity === 'CRITICAL') {
      bullets.push('Life-threatening indicators present: "unconscious", "not breathing", "bleeding"');
      bullets.push('Immediate response required');
    } else if (callData.severity === 'HIGH') {
      bullets.push('Serious but not immediately life-threatening');
      bullets.push('Requires urgent but not emergency response');
    } else if (callData.severity === 'MEDIUM') {
      bullets.push('Moderate risk or injury detected');
      bullets.push('Standard emergency response appropriate');
    } else if (callData.severity === 'LOW') {
      bullets.push('Minor issue detected');
      bullets.push('Routine response sufficient');
    }
    
    return bullets;
  };

  const explanationBullets = generateExplanationBullets(callData);

  return (
    <div className="bg-gray-800 rounded-lg shadow-lg h-full">
      <div className="p-4 border-b border-gray-700">
        <h2 className="text-lg font-semibold text-white">Explainability Panel</h2>
      </div>
      
      <div className="p-4 space-y-4">
        {callData ? (
          <>
            {/* Why Model Decided Classification */}
            <div>
              <h3 className="text-sm font-medium text-gray-300 mb-2">Why Classification Was Made</h3>
              <div className="bg-gray-900 rounded p-3 text-sm space-y-2">
                {explanationBullets.length > 0 ? (
                  explanationBullets.map((bullet, index) => (
                    <div key={index} className="flex items-start">
                      <span className="text-emergency-green mr-2">•</span>
                      <span>{bullet}</span>
                    </div>
                  ))
                ) : (
                  <p>Processing explanation...</p>
                )}
              </div>
            </div>

            {/* Highlighted Phrases */}
            <div>
              <h3 className="text-sm font-medium text-gray-300 mb-2">Highlighted Key Phrases</h3>
              <div 
                className="bg-gray-900 rounded p-3 text-sm max-h-32 overflow-y-auto prose prose-invert max-w-none"
                dangerouslySetInnerHTML={{ 
                  __html: highlightKeyPhrases(
                    callData.input_text || callData.transcript || '', 
                    callData.explanation || ''
                  ) 
                }}
              />
            </div>

            {/* Model Confidence */}
            <div>
              <h3 className="text-sm font-medium text-gray-300 mb-2">Model Confidence</h3>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Overall Confidence</span>
                  <span className="font-medium">
                    {callData.confidence ? 
                      `${Math.round(callData.confidence * 100)}%` : 'Processing...'}
                  </span>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-2">
                  <div 
                    className="bg-emergency-green h-2 rounded-full transition-all duration-500"
                    style={{ 
                      width: `${callData.confidence ? 
                        Math.round(callData.confidence * 100) : 75}%` 
                    }}
                  ></div>
                </div>
              </div>
            </div>

            {/* Transparency Note */}
            <div className="border-l-4 border-emergency-blue pl-4 py-2 bg-gray-900 rounded">
              <h3 className="text-sm font-medium text-emergency-blue mb-1">AI Transparency</h3>
              <p className="text-xs text-gray-300">
                This decision was made using NLP models trained on emergency call patterns. 
                The AI highlights key phrases that influenced its decision for dispatcher review.
              </p>
            </div>
          </>
        ) : (
          <div className="text-center py-8 text-gray-500">
            <p>No explanation data available</p>
            <p className="text-sm mt-2">Simulate a call to see AI explanations</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ExplainabilityPanel;