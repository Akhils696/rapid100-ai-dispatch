import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import CallPanel from './components/CallPanel';
import SummaryPanel from './components/SummaryPanel';
import RoutingPanel from './components/RoutingPanel';
import ExplainabilityPanel from './components/ExplainabilityPanel';
import TimelineView from './components/TimelineView';

const App = () => {
  const [currentCall, setCurrentCall] = useState(null);
  const [callHistory, setCallHistory] = useState([]);
  const [isListening, setIsListening] = useState(false);
  const [activeTab, setActiveTab] = useState('dashboard');
  
  // Audio recording state
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const [audioChunks, setAudioChunks] = useState([]);
  const [callId, setCallId] = useState(null);
  const [webSocket, setWebSocket] = useState(null);
  
  const audioRef = useRef(null);
  const wsRef = useRef(null);

  // Emergency call scenarios for simulation
  const emergencyScenarios = [
    { id: 'medical', title: 'Medical Emergency', description: 'Unconscious person not breathing' },
    { id: 'fire', title: 'Fire Emergency', description: 'House fire with smoke' },
    { id: 'crime', title: 'Crime in Progress', description: 'Break-in with gunshots' },
    { id: 'accident', title: 'Traffic Accident', description: 'Multi-car collision' },
    { id: 'disaster', title: 'Natural Disaster', description: 'Tornado warning' }
  ];

  // Simulate incoming call
  const simulateCall = async (scenarioId) => {
    try {
      const response = await axios.get(`http://localhost:8000/api/simulate-call/${scenarioId}`);
      const callData = {
        ...response.data,
        call_id: `sim-${Date.now()}`,
        timestamp: new Date().toISOString()
      };
      
      setCurrentCall(callData);
      setCallHistory(prev => [callData, ...prev.slice(0, 9)]); // Keep last 10 calls
    } catch (error) {
      console.error('Error simulating call:', error);
    }
  };

  // Fetch call logs
  const fetchCallLogs = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/logs');
      setCallHistory(response.data.logs || []);
    } catch (error) {
      console.error('Error fetching logs:', error);
    }
  };

  useEffect(() => {
    fetchCallLogs();
  }, []);
  
  // Function to start voice recording
  const startVoiceInput = async () => {
    try {
      // Generate a unique call ID
      const newCallId = `call_${Date.now()}`;
      setCallId(newCallId);
      
      // Request microphone access with specific audio constraints
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          sampleRate: 16000,  // Set sample rate to 16kHz for better compatibility
          channelCount: 1,    // Mono audio
          volume: 1.0
        } 
      });
      
      // Create MediaRecorder with audio/wav mimeType for better compatibility
      const mediaOptions = {
        mimeType: 'audio/wav'
      };
      
      // Check if the mimeType is supported
      const recorder = MediaRecorder.isTypeSupported('audio/wav') 
        ? new MediaRecorder(stream, mediaOptions)
        : new MediaRecorder(stream);
      
      setMediaRecorder(recorder);
      
      // Create WebSocket connection
      const ws = new WebSocket(`ws://127.0.0.1:8000/ws/transcribe/${newCallId}`);
      wsRef.current = ws;
      setWebSocket(ws);
      
      ws.onopen = () => {
        console.log('Connected to WebSocket successfully');
        setIsListening(true);
      };
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          setCurrentCall(data);
          
          // Update call history
          setCallHistory(prev => [data, ...prev.slice(0, 9)]);
        } catch (e) {
          console.error('Error parsing WebSocket message:', e);
        }
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
      
      ws.onclose = (event) => {
        console.log('WebSocket connection closed:', event.code, event.reason);
        setIsListening(false);
      };
      
      // Handle audio data
      recorder.ondataavailable = async (event) => {
        if (event.data.size > 0) {
          console.log('Sending audio chunk, size:', event.data.size);
          
          // Convert audio blob to ArrayBuffer for WebSocket transmission
          const arrayBuffer = await event.data.arrayBuffer();
          
          // Send audio chunk to WebSocket
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(arrayBuffer);
            console.log('Audio chunk sent to WebSocket');
          } else {
            console.warn('WebSocket not open, dropping audio chunk');
          }
        }
      };
      
      // Handle recording errors
      recorder.onerror = (event) => {
        console.error('MediaRecorder error:', event);
      };
      
      // Start recording with small time intervals for real-time processing
      recorder.start(1000); // Collect data every 1 second
      
    } catch (error) {
      console.error('Error accessing microphone:', error);
    }
  };
  
  // Function to stop voice recording
  const stopVoiceInput = () => {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
      mediaRecorder.stop();
    }
    
    if (wsRef.current) {
      wsRef.current.close();
    }
    
    setIsListening(false);
    setMediaRecorder(null);
    setWebSocket(null);
    setCallId(null);
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-emergency-red">RAPID-100</h1>
            <p className="text-sm text-gray-400">Real-time AI for Priority Incident Dispatch</p>
          </div>
          <div className="flex space-x-4">
            <button 
              onClick={() => setActiveTab('dashboard')}
              className={`px-4 py-2 rounded ${activeTab === 'dashboard' ? 'bg-emergency-red text-white' : 'bg-gray-700 hover:bg-gray-600'}`}
            >
              Dashboard
            </button>
            <button 
              onClick={() => setActiveTab('logs')}
              className={`px-4 py-2 rounded ${activeTab === 'logs' ? 'bg-emergency-red text-white' : 'bg-gray-700 hover:bg-gray-600'}`}
            >
              Call Logs
            </button>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-6">
        {activeTab === 'dashboard' ? (
          <>
            {/* Action Bar */}
            <div className="mb-6 bg-gray-800 rounded-lg p-4">
              <div className="flex flex-wrap gap-4 items-center">
                <span className="font-medium">Simulate Emergency Call:</span>
                {emergencyScenarios.map(scenario => (
                  <button
                    key={scenario.id}
                    onClick={() => simulateCall(scenario.id)}
                    className="px-4 py-2 bg-emergency-red hover:bg-red-700 rounded-md text-sm font-medium transition-colors"
                  >
                    {scenario.title}
                  </button>
                ))}
                <div className="ml-auto flex items-center space-x-2">
                  <button
                    onClick={isListening ? stopVoiceInput : startVoiceInput}
                    className={`px-4 py-2 rounded-md font-medium transition-colors ${isListening ? 'bg-red-600 hover:bg-red-700' : 'bg-emerald-600 hover:bg-emerald-700'}`}
                  >
                    {isListening ? (
                      <>
                        <span className="mr-2">⏹️</span> Stop Listening
                      </>
                    ) : (
                      <>
                        <span className="mr-2">🎤</span> Voice Input
                      </>
                    )}
                  </button>
                  <div className={`w-3 h-3 rounded-full ${isListening ? 'bg-green-500 animate-pulse' : 'bg-gray-500'}`}></div>
                  <span>{isListening ? 'Listening...' : 'Standby'}</span>
                </div>
              </div>
            </div>

            {/* Main Dashboard Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
              {/* Live Call Panel */}
              <div className="lg:col-span-1">
                <CallPanel callData={currentCall} />
              </div>

              {/* Summary Panel */}
              <div className="lg:col-span-1">
                <SummaryPanel callData={currentCall} />
              </div>
            </div>

            {/* Bottom Panels */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Routing Panel */}
              <div>
                <RoutingPanel callData={currentCall} />
              </div>

              {/* Explainability Panel */}
              <div>
                <ExplainabilityPanel callData={currentCall} />
              </div>

              {/* Timeline View */}
              <div>
                <TimelineView callData={currentCall} />
              </div>
            </div>
          </>
        ) : (
          /* Call Logs Tab */
          <div className="bg-gray-800 rounded-lg p-6">
            <h2 className="text-xl font-bold mb-4">Recent Call Logs</h2>
            <div className="space-y-4 max-h-96 overflow-y-auto">
              {callHistory.length > 0 ? (
                callHistory.map((log, index) => (
                  <div key={index} className="bg-gray-700 p-4 rounded-lg">
                    <div className="flex justify-between items-start">
                      <div>
                        <h3 className="font-medium">{log.predicted_class} - {log.severity}</h3>
                        <p className="text-sm text-gray-400">{new Date(log.timestamp).toLocaleString()}</p>
                      </div>
                      <span className={`px-2 py-1 rounded text-xs ${
                        log.severity === 'CRITICAL' ? 'bg-red-900 text-red-200' :
                        log.severity === 'HIGH' ? 'bg-orange-900 text-orange-200' :
                        log.severity === 'MEDIUM' ? 'bg-yellow-900 text-yellow-200' :
                        'bg-green-900 text-green-200'
                      }`}>
                        {log.severity}
                      </span>
                    </div>
                    <p className="mt-2 text-sm">{log.transcript}</p>
                    <div className="mt-2 flex justify-between text-xs text-gray-400">
                      <span>Routing: {log.routing_decision.department}</span>
                      <span>Conf: {(log.confidence * 100).toFixed(1)}%</span>
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-gray-400">No call logs available</p>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default App;