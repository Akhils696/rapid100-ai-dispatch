import React from 'react';

const SummaryPanel = ({ callData }) => {
  // Risk indicators based on keywords in transcript
  const getRiskIndicators = (transcript, emergencyType) => {
    if (!transcript) return [];
    
    const indicators = [];
    const textLower = transcript.toLowerCase();
    
    // Add risk indicators based on emergency type
    switch (emergencyType) {
      case 'MEDICAL':
        if (textLower.includes('unconscious') || textLower.includes('not breathing')) {
          indicators.push({ text: 'Life-threatening condition', level: 'critical' });
        }
        if (textLower.includes('heart') || textLower.includes('stroke')) {
          indicators.push({ text: 'Cardiovascular emergency', level: 'high' });
        }
        if (textLower.includes('bleeding') || textLower.includes('blood')) {
          indicators.push({ text: 'Significant bleeding', level: 'high' });
        }
        break;
        
      case 'FIRE':
        if (textLower.includes('smoke') || textLower.includes('inhale')) {
          indicators.push({ text: 'Smoke inhalation risk', level: 'critical' });
        }
        if (textLower.includes('spread') || textLower.includes('multiple')) {
          indicators.push({ text: 'Fire spread potential', level: 'high' });
        }
        break;
        
      case 'CRIME':
        if (textLower.includes('gun') || textLower.includes('weapon')) {
          indicators.push({ text: 'Weapon involved', level: 'critical' });
        }
        if (textLower.includes('multiple') || textLower.includes('group')) {
          indicators.push({ text: 'Multiple perpetrators', level: 'high' });
        }
        break;
        
      case 'ACCIDENT':
        if (textLower.includes('multiple cars') || textLower.includes('pileup')) {
          indicators.push({ text: 'Multiple vehicles involved', level: 'high' });
        }
        if (textLower.includes('trapped') || textLower.includes('extrication')) {
          indicators.push({ text: 'Person trapped', level: 'high' });
        }
        break;
        
      default:
        break;
    }
    
    // General risk indicators
    if (textLower.includes('child') || textLower.includes('baby')) {
      indicators.push({ text: 'Child involved', level: 'high' });
    }
    if (textLower.includes('pregnant') || textLower.includes('pregnancy')) {
      indicators.push({ text: 'Pregnant person involved', level: 'high' });
    }
    if (textLower.includes('elderly') || textLower.includes('old person')) {
      indicators.push({ text: 'Elderly person involved', level: 'medium' });
    }
    
    return indicators;
  };

  const riskIndicators = callData ? getRiskIndicators(callData.input_text || callData.transcript, callData.predicted_type || callData.predicted_class) : [];

  // Determine indicator color
  const getIndicatorColor = (level) => {
    switch (level) {
      case 'critical': return 'bg-red-900 text-red-200';
      case 'high': return 'bg-orange-900 text-orange-200';
      case 'medium': return 'bg-yellow-900 text-yellow-200';
      case 'low': return 'bg-blue-900 text-blue-200';
      default: return 'bg-gray-700 text-gray-200';
    }
  };

  return (
    <div className="bg-gray-800 rounded-lg shadow-lg h-full">
      <div className="p-4 border-b border-gray-700">
        <h2 className="text-lg font-semibold text-white">Structured Summary Panel</h2>
      </div>
      
      <div className="p-4 space-y-4">
        {callData ? (
          <>
            {/* Emergency Type */}
            <div>
              <h3 className="text-sm font-medium text-gray-300 mb-1">Emergency Type</h3>
              <span className="inline-block bg-emergency-red text-white text-sm px-3 py-1 rounded-full">
                {callData.predicted_type || callData.predicted_class}
              </span>
            </div>

            {/* Priority Score */}
            <div>
              <h3 className="text-sm font-medium text-gray-300 mb-1">Priority Score</h3>
              <div className="flex items-center space-x-2">
                <span className={`text-lg font-bold ${
                  callData.severity === 'CRITICAL' ? 'text-red-400' :
                  callData.severity === 'HIGH' ? 'text-orange-400' :
                  callData.severity === 'MEDIUM' ? 'text-yellow-400' : 'text-green-400'
                }`}>
                  {callData.severity}
                </span>
                <span className="text-xs text-gray-400">
                  Confidence: {callData.routing_decision?.confidence ? 
                    `${Math.round(callData.routing_decision.confidence * 100)}%` : 'N/A'}
                </span>
              </div>
            </div>

            {/* Extracted Location */}
            <div>
              <h3 className="text-sm font-medium text-gray-300 mb-1">Location</h3>
              <p className="text-emergency-green">
                {callData.location || callData.extracted_entities?.locations?.[0] || 'Location not specified'}
              </p>
            </div>

            {/* Key Risk Indicators */}
            <div>
              <h3 className="text-sm font-medium text-gray-300 mb-2">Key Risk Indicators</h3>
              {riskIndicators.length > 0 ? (
                <div className="space-y-2">
                  {riskIndicators.map((indicator, index) => (
                    <div key={index} className={`text-xs px-2 py-1 rounded ${getIndicatorColor(indicator.level)}`}>
                      {indicator.text}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500 text-sm">No specific risk indicators identified</p>
              )}
            </div>

            {/* Suggested Routing */}
            <div>
              <h3 className="text-sm font-medium text-gray-300 mb-1">Suggested Routing</h3>
              <div className="bg-gray-900 rounded p-3">
                <p className="text-emergency-green font-medium">
                  {callData.routing_decision?.department || 'Emergency Services'}
                </p>
                <p className="text-xs text-gray-400 mt-1">
                  AI Suggested – Awaiting Human Confirmation
                </p>
              </div>
            </div>
          </>
        ) : (
          <div className="text-center py-8 text-gray-500">
            <p>No active call data</p>
            <p className="text-sm mt-2">Simulate a call to see structured summary</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default SummaryPanel;