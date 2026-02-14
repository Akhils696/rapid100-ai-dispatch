import React from 'react';

const RoutingPanel = ({ callData }) => {
  // Determine department color based on type
  const getDepartmentColor = (department) => {
    if (!department) return 'bg-gray-700';
    
    const dept = department.toLowerCase();
    if (dept.includes('fire')) return 'bg-red-900';
    if (dept.includes('police') || dept.includes('crime')) return 'bg-blue-900';
    if (dept.includes('ambulance') || dept.includes('medical')) return 'bg-green-900';
    if (dept.includes('emergency')) return 'bg-purple-900';
    
    return 'bg-gray-700';
  };

  return (
    <div className="bg-gray-800 rounded-lg shadow-lg h-full">
      <div className="p-4 border-b border-gray-700">
        <h2 className="text-lg font-semibold text-white">Routing Panel</h2>
      </div>
      
      <div className="p-4 space-y-4">
        {callData ? (
          <>
            {/* Recommended Department */}
            <div>
              <h3 className="text-sm font-medium text-gray-300 mb-2">Recommended Department</h3>
              <div className={`${getDepartmentColor(callData.routing_decision?.department)} rounded-lg p-4`}>
                <h4 className="text-lg font-bold text-white">
                  {callData.routing_decision?.department || 'Emergency Services'}
                </h4>
                <p className="text-sm text-gray-300 mt-1">
                  Best suited for this type of emergency
                </p>
              </div>
            </div>

            {/* Confidence Score */}
            <div>
              <h3 className="text-sm font-medium text-gray-300 mb-2">Confidence Score</h3>
              <div className="flex items-center space-x-3">
                <div className="flex-1 bg-gray-700 rounded-full h-3">
                  <div 
                    className="bg-emergency-green h-3 rounded-full transition-all duration-500"
                    style={{ 
                      width: `${callData.routing_decision?.confidence ? 
                        Math.round(callData.routing_decision.confidence * 100) : 80}%` 
                    }}
                  ></div>
                </div>
                <span className="text-sm font-medium text-white">
                  {callData.routing_decision?.confidence ? 
                    `${Math.round(callData.routing_decision.confidence * 100)}%` : '80%'}
                </span>
              </div>
            </div>

            {/* Routing Justification */}
            <div>
              <h3 className="text-sm font-medium text-gray-300 mb-2">Routing Justification</h3>
              <div className="bg-gray-900 rounded p-3 text-sm">
                {callData.predicted_class === 'FIRE' && (
                  <p>Fire emergency detected. Route to Fire Department for immediate response.</p>
                )}
                {callData.predicted_class === 'MEDICAL' && (
                  <p>Medical emergency detected. Route to Ambulance Service for medical assistance.</p>
                )}
                {callData.predicted_class === 'CRIME' && (
                  <p>Criminal activity detected. Route to Police Department for law enforcement.</p>
                )}
                {callData.predicted_class === 'ACCIDENT' && (
                  <p>Traffic accident detected. Route to Emergency Services for multi-agency response.</p>
                )}
                {callData.predicted_class === 'DISASTER' && (
                  <p>Natural disaster detected. Route to Emergency Management for coordination.</p>
                )}
                {(!callData.predicted_class || callData.predicted_class === 'UNKNOWN') && (
                  <p>Emergency type unclear. Route to General Emergency Services for assessment.</p>
                )}
              </div>
            </div>

            {/* Human Confirmation */}
            <div className="border-l-4 border-emergency-yellow pl-4 py-2 bg-gray-900 rounded">
              <h3 className="text-sm font-medium text-emergency-yellow mb-1">Action Required</h3>
              <p className="text-xs text-gray-300">
                AI Suggested – Awaiting Human Confirmation<br />
                Dispatcher must review and approve routing decision
              </p>
            </div>
          </>
        ) : (
          <div className="text-center py-8 text-gray-500">
            <p>No routing data available</p>
            <p className="text-sm mt-2">Simulate a call to see routing recommendations</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default RoutingPanel;