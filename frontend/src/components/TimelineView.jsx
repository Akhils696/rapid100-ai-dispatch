import React from 'react';

const TimelineView = ({ callData }) => {
  // Create timeline steps based on call data
  const getTimelineSteps = (callData) => {
    if (!callData) {
      return [
        { step: 'Speech', status: 'pending', description: 'Waiting for emergency call audio' },
        { step: 'Transcript', status: 'pending', description: 'Transcription will appear here' },
        { step: 'Classification', status: 'pending', description: 'Emergency type detection' },
        { step: 'Severity', status: 'pending', description: 'Priority level assignment' },
        { step: 'Routing', status: 'pending', description: 'Department assignment' }
      ];
    }
    
    return [
      { 
        step: 'Speech', 
        status: 'completed', 
        description: 'Audio received from emergency caller',
        time: callData.timestamp ? new Date(callData.timestamp).toLocaleTimeString() : 'Just now'
      },
      { 
        step: 'Transcript', 
        status: 'completed', 
        description: callData.input_text || callData.transcript || 'Transcribed speech content',
        time: callData.timestamp ? new Date(Date.parse(callData.timestamp) + 500).toLocaleTimeString() : 'Just now'
      },
      { 
        step: 'Classification', 
        status: 'completed', 
        description: `Detected ${callData.predicted_type || callData.predicted_class} emergency`,
        time: callData.timestamp ? new Date(Date.parse(callData.timestamp) + 1000).toLocaleTimeString() : 'Just now'
      },
      { 
        step: 'Severity', 
        status: 'completed', 
        description: `Assigned ${callData.severity} severity level`,
        time: callData.timestamp ? new Date(Date.parse(callData.timestamp) + 1500).toLocaleTimeString() : 'Just now'
      },
      { 
        step: 'Routing', 
        status: 'completed', 
        description: `Suggested routing to ${callData.routing_decision?.department || 'Emergency Services'}`,
        time: callData.timestamp ? new Date(Date.parse(callData.timestamp) + 2000).toLocaleTimeString() : 'Just now'
      }
    ];
  };

  const timelineSteps = getTimelineSteps(callData);

  return (
    <div className="bg-gray-800 rounded-lg shadow-lg h-full">
      <div className="p-4 border-b border-gray-700">
        <h2 className="text-lg font-semibold text-white">AI Decision Timeline</h2>
      </div>
      
      <div className="p-4">
        <div className="space-y-4">
          {timelineSteps.map((step, index) => (
            <div key={index} className="flex">
              {/* Timeline connector */}
              <div className="flex flex-col items-center mr-4">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                  step.status === 'completed' ? 'bg-emergency-green text-white' : 
                  step.status === 'processing' ? 'bg-yellow-500 text-white animate-pulse' : 
                  'bg-gray-600 text-gray-400'
                }`}>
                  {step.status === 'completed' ? '✓' : index + 1}
                </div>
                {index < timelineSteps.length - 1 && (
                  <div className={`w-0.5 h-16 ${step.status === 'completed' ? 'bg-emergency-green' : 'bg-gray-600'}`}></div>
                )}
              </div>
              
              {/* Step content */}
              <div className="flex-1 pb-4">
                <div className="flex justify-between items-start">
                  <h3 className={`font-medium ${
                    step.status === 'completed' ? 'text-white' : 'text-gray-400'
                  }`}>
                    {step.step}
                  </h3>
                  {step.time && (
                    <span className="text-xs text-gray-500">{step.time}</span>
                  )}
                </div>
                <p className={`text-sm mt-1 ${
                  step.status === 'completed' ? 'text-gray-300' : 'text-gray-500'
                }`}>
                  {step.description}
                </p>
              </div>
            </div>
          ))}
        </div>
        
        {/* Total Processing Time */}
        <div className="mt-6 pt-4 border-t border-gray-700">
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-400">Total Processing Time:</span>
            <span className="text-sm font-medium text-emergency-green">~2.1s</span>
          </div>
          <div className="mt-2 w-full bg-gray-700 rounded-full h-2">
            <div 
              className="bg-gradient-to-r from-emergency-green to-emergency-yellow h-2 rounded-full"
              style={{ width: '100%' }}
            ></div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TimelineView;