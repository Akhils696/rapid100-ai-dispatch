import React from 'react';

const CallDetailModal = ({ call, onClose }) => {
  if (!call) return null;

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'CRITICAL': return 'bg-red-500';
      case 'HIGH': return 'bg-orange-500';
      case 'MEDIUM': return 'bg-yellow-500';
      case 'LOW': return 'bg-green-500';
      default: return 'bg-gray-500';
    }
  };

  const getEmergencyTypeColor = (type) => {
    switch (type) {
      case 'MEDICAL': return 'bg-blue-500';
      case 'FIRE': return 'bg-red-600';
      case 'CRIME': return 'bg-purple-500';
      case 'ACCIDENT': return 'bg-yellow-600';
      case 'DISASTER': return 'bg-orange-600';
      default: return 'bg-gray-500';
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-800 rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        {/* Modal Header */}
        <div className="p-6 border-b border-gray-700 flex justify-between items-start">
          <div>
            <h2 className="text-2xl font-bold text-white mb-2">Call Details</h2>
            <div className="flex items-center space-x-3">
              <span className={`px-3 py-1 rounded-full text-white text-sm font-medium ${getEmergencyTypeColor(call.emergency_type || call.predicted_type)}`}>
                {call.emergency_type || call.predicted_type}
              </span>
              <span className={`px-3 py-1 rounded-full text-white text-sm font-medium ${getSeverityColor(call.severity)}`}>
                {call.severity}
              </span>
              <span className="text-gray-400 text-sm">
                {new Date(call.timestamp).toLocaleString()}
              </span>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Modal Content */}
        <div className="p-6 space-y-6">
          {/* Transcript Section */}
          <div>
            <h3 className="text-lg font-semibold text-white mb-3 flex items-center">
              <span className="mr-2">📝</span>
              Call Transcript
            </h3>
            <div className="bg-gray-900 rounded-lg p-4">
              <p className="text-emergency-green font-mono text-sm leading-relaxed">
                {call.transcript || call.input_text || 'No transcript available'}
              </p>
            </div>
          </div>

          {/* Location Information */}
          {call.location && (
            <div>
              <h3 className="text-lg font-semibold text-white mb-3 flex items-center">
                <span className="mr-2">📍</span>
                Location Information
              </h3>
              <div className="bg-gray-900 rounded-lg p-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <p className="text-gray-400 text-sm">Address</p>
                    <p className="text-white font-medium">{call.location}</p>
                  </div>
                  {call.location_data && (
                    <>
                      <div>
                        <p className="text-gray-400 text-sm">Coordinates</p>
                        <p className="text-white font-mono">
                          {call.location_data.latitude?.toFixed(6)}, {call.location_data.longitude?.toFixed(6)}
                        </p>
                      </div>
                      <div>
                        <p className="text-gray-400 text-sm">Area</p>
                        <p className="text-white">{call.location_data.area || 'Unknown'}</p>
                      </div>
                    </>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Analysis Information */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Routing Decision */}
            {call.routing_decision && (
              <div>
                <h3 className="text-lg font-semibold text-white mb-3 flex items-center">
                  <span className="mr-2">🎯</span>
                  Routing Decision
                </h3>
                <div className="bg-gray-900 rounded-lg p-4">
                  <div className="space-y-2">
                    <div>
                      <p className="text-gray-400 text-sm">Department</p>
                      <p className="text-white font-medium">{call.routing_decision.department}</p>
                    </div>
                    <div>
                      <p className="text-gray-400 text-sm">Confidence</p>
                      <p className="text-white">
                        {(call.routing_decision.confidence * 100).toFixed(1)}%
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Audio Metrics */}
            {(call.audio_metrics || call.noise_confidence) && (
              <div>
                <h3 className="text-lg font-semibold text-white mb-3 flex items-center">
                  <span className="mr-2">🔊</span>
                  Audio Quality
                </h3>
                <div className="bg-gray-900 rounded-lg p-4">
                  <div className="space-y-2">
                    {call.audio_metrics?.level !== undefined && (
                      <div>
                        <p className="text-gray-400 text-sm">Audio Level</p>
                        <p className="text-white">{Math.round(call.audio_metrics.level * 100)}%</p>
                      </div>
                    )}
                    {call.audio_metrics?.quality_score !== undefined && (
                      <div>
                        <p className="text-gray-400 text-sm">Quality Score</p>
                        <p className="text-white">{Math.round(call.audio_metrics.quality_score * 100)}%</p>
                      </div>
                    )}
                    {call.noise_confidence !== undefined && (
                      <div>
                        <p className="text-gray-400 text-sm">Noise Confidence</p>
                        <p className="text-white">{Math.round(call.noise_confidence * 100)}%</p>
                      </div>
                    )}
                    {call.emotion_meter !== undefined && (
                      <div>
                        <p className="text-gray-400 text-sm">Emotion Intensity</p>
                        <p className="text-white">{Math.round(call.emotion_meter * 100)}%</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Additional Information */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Explanation */}
            {call.explanation && (
              <div>
                <h3 className="text-lg font-semibold text-white mb-3 flex items-center">
                  <span className="mr-2">💡</span>
                  Explanation
                </h3>
                <div className="bg-gray-900 rounded-lg p-4">
                  <p className="text-gray-300 text-sm">{call.explanation}</p>
                </div>
              </div>
            )}

            {/* Metadata */}
            <div>
              <h3 className="text-lg font-semibold text-white mb-3 flex items-center">
                <span className="mr-2">📊</span>
                Metadata
              </h3>
              <div className="bg-gray-900 rounded-lg p-4">
                <div className="space-y-2">
                  {call.language && (
                    <div>
                      <p className="text-gray-400 text-sm">Language</p>
                      <p className="text-white capitalize">{call.language}</p>
                    </div>
                  )}
                  {call.confidence !== undefined && (
                    <div>
                      <p className="text-gray-400 text-sm">Classification Confidence</p>
                      <p className="text-white">{(call.confidence * 100).toFixed(1)}%</p>
                    </div>
                  )}
                  <div>
                    <p className="text-gray-400 text-sm">Call ID</p>
                    <p className="text-white font-mono text-sm">{call.call_id || 'Unknown'}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Extracted Entities */}
          {call.extracted_entities && Object.keys(call.extracted_entities).length > 0 && (
            <div>
              <h3 className="text-lg font-semibold text-white mb-3 flex items-center">
                <span className="mr-2">🔍</span>
                Extracted Information
              </h3>
              <div className="bg-gray-900 rounded-lg p-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {Object.entries(call.extracted_entities).map(([key, value]) => (
                    <div key={key} className="bg-gray-800 rounded p-3">
                      <p className="text-gray-400 text-sm capitalize">{key.replace(/_/g, ' ')}</p>
                      <p className="text-white">
                        {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="p-6 border-t border-gray-700 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-md transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default CallDetailModal;