import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import CallPanel from './components/CallPanel';
import SummaryPanel from './components/SummaryPanel';
import RoutingPanel from './components/RoutingPanel';
import ExplainabilityPanel from './components/ExplainabilityPanel';
import TimelineView from './components/TimelineView';
import MapPanel from './components/MapPanel';
import CallDetailModal from './components/CallDetailModal';

const App = () => {
  const [currentCall, setCurrentCall] = useState(null);
  const [callHistory, setCallHistory] = useState([]);
  const [isListening, setIsListening] = useState(false);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [selectedCall, setSelectedCall] = useState(null);
  const [showCallDetail, setShowCallDetail] = useState(false);
  
  // Audio recording state
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const [audioContext, setAudioContext] = useState(null);
  const [audioAnalyser, setAudioAnalyser] = useState(null);
  const [audioChunks, setAudioChunks] = useState([]);
  const [callId, setCallId] = useState(null);
  const [webSocket, setWebSocket] = useState(null);
  const [audioLevel, setAudioLevel] = useState(0);
  const [isNoiseFiltering, setIsNoiseFiltering] = useState(true);
  const [selectedLanguage, setSelectedLanguage] = useState('en');
  
  const audioRef = useRef(null);
  const wsRef = useRef(null);
  const animationRef = useRef(null);

  // Emergency call scenarios for simulation
  const emergencyScenarios = [
    { id: 'medical', title: 'Medical Emergency', description: 'Unconscious person not breathing' },
    { id: 'fire', title: 'Fire Emergency', description: 'House fire with smoke' },
    { id: 'crime', title: 'Crime in Progress', description: 'Break-in with gunshots' },
    { id: 'accident', title: 'Traffic Accident', description: 'Multi-car collision' },
    { id: 'disaster', title: 'Natural Disaster', description: 'Tornado warning' }
  ];

  // Language options for multilingual support
  const languageOptions = [
    { code: 'en', name: 'English', flag: '🇺🇸' },
    { code: 'es', name: 'Spanish', flag: '🇪🇸' },
    { code: 'fr', name: 'French', flag: '🇫🇷' },
    { code: 'de', name: 'German', flag: '🇩🇪' },
    { code: 'hi', name: 'Hindi', flag: '🇮🇳' },
    { code: 'zh', name: 'Chinese', flag: '🇨🇳' },
    { code: 'ja', name: 'Japanese', flag: '🇯🇵' },
    { code: 'ar', name: 'Arabic', flag: '🇸🇦' }
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
      const response = await axios.get('http://localhost:8000/api/logs', {
        timeout: 5000 // 5 second timeout
      });
      setCallHistory(response.data.logs || []);
    } catch (error) {
      console.error('Error fetching logs:', error);
      // Don't show alert for logs fetching - it's not critical
      // Just silently fail and continue
    }
  };

  useEffect(() => {
    // Try to fetch logs, retry once if failed
    const attemptFetch = async (retry = true) => {
      try {
        await fetchCallLogs();
      } catch (error) {
        if (retry) {
          console.log('First logs fetch failed, retrying in 2 seconds...');
          setTimeout(() => attemptFetch(false), 2000);
        }
      }
    };
    
    attemptFetch();
  }, []);
  
  // Function to start voice recording with enhanced audio processing
  const startVoiceInput = async () => {
    try {
      // Generate a unique call ID
      const newCallId = `call_${Date.now()}`;
      setCallId(newCallId);
      
      // Request microphone access with enhanced audio constraints
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          sampleRate: 48000,  // Higher sample rate for better quality
          channelCount: 1,    // Mono audio
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          latency: 0,
          volume: 1.0
        } 
      });
      
      // Initialize Web Audio API for advanced processing
      const context = new (window.AudioContext || window.webkitAudioContext)({
        sampleRate: 48000
      });
      setAudioContext(context);
      
      // Create audio processing nodes
      const source = context.createMediaStreamSource(stream);
      const analyser = context.createAnalyser();
      analyser.fftSize = 256;
      
      // Create noise reduction filter
      const filter = context.createBiquadFilter();
      filter.type = 'bandpass';
      filter.frequency.value = 1000; // Center frequency
      filter.Q.value = 1.0; // Quality factor
      
      // Connect audio processing chain
      source.connect(filter);
      filter.connect(analyser);
      
      setAudioAnalyser(analyser);
      
      // Start audio level monitoring
      const bufferLength = analyser.frequencyBinCount;
      const dataArray = new Uint8Array(bufferLength);
      
      const updateAudioLevel = () => {
        analyser.getByteFrequencyData(dataArray);
        const average = dataArray.reduce((a, b) => a + b) / bufferLength;
        setAudioLevel(average / 255); // Normalize to 0-1
        
        if (isListening) {
          animationRef.current = requestAnimationFrame(updateAudioLevel);
        }
      };
      
      updateAudioLevel();
      
      // Create MediaRecorder with enhanced settings
      const mediaOptions = {
        mimeType: 'audio/webm;codecs=opus' // Better compression and quality
      };
      
      // Check if the mimeType is supported
      const recorder = MediaRecorder.isTypeSupported('audio/webm;codecs=opus') 
        ? new MediaRecorder(stream, mediaOptions)
        : new MediaRecorder(stream);
      
      setMediaRecorder(recorder);
      
      // Create WebSocket connection with language parameter
      const ws = new WebSocket(`ws://127.0.0.1:8000/ws/transcribe/${newCallId}?lang=${selectedLanguage}`);
      wsRef.current = ws;
      setWebSocket(ws);
      
      // Connection timeout handling
      const connectionTimeout = setTimeout(() => {
        if (ws.readyState === WebSocket.CONNECTING) {
          console.error('WebSocket connection timeout');
          ws.close();
          alert('Connection timeout. Please check if the backend server is running.');
          // Clean up
          setIsListening(false);
          setMediaRecorder(null);
          setWebSocket(null);
          setCallId(null);
          if (context) {
            context.close();
          }
        }
      }, 10000); // 10 second timeout
      
      // Queue for messages while connecting
      const messageQueue = [];
      
      // Cleanup function
      const cleanup = () => {
        clearTimeout(connectionTimeout);
        if (animationRef.current) {
          cancelAnimationFrame(animationRef.current);
        }
        // Safely close audio context
        if (context && context.state !== 'closed') {
          context.close().catch(err => console.warn('Error closing audio context:', err));
        }
      };
      
      // Store cleanup function for later use
      wsRef.current.cleanup = cleanup;
      
      // Function to send queued messages
      const sendQueuedMessages = () => {
        while (messageQueue.length > 0 && ws.readyState === WebSocket.OPEN) {
          const message = messageQueue.shift();
          ws.send(message);
          console.log('Sent queued message');
        }
      };
      
      // Enhanced send function with connection state checking
      const safeSend = (data) => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(data);
        } else if (ws.readyState === WebSocket.CONNECTING) {
          messageQueue.push(data);
          console.log('Message queued, WebSocket still connecting');
        } else {
          console.warn('WebSocket not in valid state for sending:', ws.readyState);
        }
      };
      
      ws.onopen = () => {
        console.log('Connected to WebSocket successfully');
        setIsListening(true);
        
        // Send initial configuration
        safeSend(JSON.stringify({
          type: 'config',
          language: selectedLanguage,
          noise_filtering: isNoiseFiltering,
          sample_rate: 48000
        }));
        
        // Send any queued messages
        sendQueuedMessages();
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
        // Only show alert if we were actually trying to connect/listen
        if (isListening || !callId) {
          alert('Connection error. Please check if the backend server is running and try again.');
        }
        // Clean up on error
        cleanup();
        setIsListening(false);
        setMediaRecorder(null);
        setWebSocket(null);
        setCallId(null);
      };
      
      ws.onclose = (event) => {
        console.log('WebSocket connection closed:', event.code, event.reason);
        setIsListening(false);
        cleanup(); // Use the cleanup function
      };
      
      // Handle audio data with enhanced processing
      recorder.ondataavailable = async (event) => {
        if (event.data.size > 0 && isListening) {
          console.log('Processing audio chunk, size:', event.data.size);
          
          // Convert audio blob to ArrayBuffer for WebSocket transmission
          const arrayBuffer = await event.data.arrayBuffer();
          
          // Send audio chunk to WebSocket with metadata
          safeSend(JSON.stringify({
            type: 'audio_chunk',
            data: Array.from(new Uint8Array(arrayBuffer)),
            timestamp: Date.now(),
            audio_level: audioLevel
          }));
        }
      };
      
      // Handle recording errors
      recorder.onerror = (event) => {
        console.error('MediaRecorder error:', event);
        alert('Recording error. Please try again.');
      };
      
      // Start recording with smaller intervals for real-time processing
      recorder.start(500); // Collect data every 500ms for better real-time performance
      
    } catch (error) {
      console.error('Error accessing microphone:', error);
      alert('Error accessing microphone. Please check permissions and try again.');
    }
  };
  
  // Function to stop voice recording
  const stopVoiceInput = () => {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
      mediaRecorder.stop();
    }
    
    if (wsRef.current) {
      // Use cleanup function if available
      if (wsRef.current.cleanup) {
        wsRef.current.cleanup();
      }
      if (wsRef.current.readyState !== WebSocket.CLOSED) {
        wsRef.current.close();
      }
    }
    
    // Safely clean up Web Audio API
    if (audioContext && audioContext.state !== 'closed') {
      audioContext.close().catch(err => console.warn('Error closing audio context:', err));
    }
    setAudioContext(null);
    
    setIsListening(false);
    setMediaRecorder(null);
    setWebSocket(null);
    setCallId(null);
    setAudioLevel(0);
  };
  
  // Function to show call details
  const showCallDetails = (call) => {
    setSelectedCall(call);
    setShowCallDetail(true);
  };
  
  // Function to close call details
  const closeCallDetails = () => {
    setShowCallDetail(false);
    setSelectedCall(null);
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
                <div className="ml-auto flex items-center space-x-4">
                  {/* Language Selection */}
                  <div className="flex items-center space-x-2">
                    <span className="text-sm text-gray-300">Language:</span>
                    <select 
                      value={selectedLanguage}
                      onChange={(e) => setSelectedLanguage(e.target.value)}
                      disabled={isListening}
                      className="bg-gray-700 text-white px-2 py-1 rounded text-sm border border-gray-600 disabled:opacity-50"
                    >
                      {languageOptions.map(lang => (
                        <option key={lang.code} value={lang.code}>
                          {lang.flag} {lang.name}
                        </option>
                      ))}
                    </select>
                  </div>
                  
                  {/* Noise Filtering Toggle */}
                  <div className="flex items-center space-x-2">
                    <span className="text-sm text-gray-300">Noise Filter:</span>
                    <button
                      onClick={() => setIsNoiseFiltering(!isNoiseFiltering)}
                      disabled={isListening}
                      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${isNoiseFiltering ? 'bg-emerald-600' : 'bg-gray-600'} disabled:opacity-50`}
                    >
                      <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${isNoiseFiltering ? 'translate-x-6' : 'translate-x-1'}`}></span>
                    </button>
                  </div>
                  
                  {/* Audio Level Visualization */}
                  {isListening && (
                    <div className="flex items-center space-x-2">
                      <div className="flex space-x-1 h-6 items-end">
                        {[...Array(10)].map((_, i) => (
                          <div 
                            key={i}
                            className={`w-1 bg-emerald-500 transition-all duration-100 ${i < Math.floor(audioLevel * 10) ? 'h-4' : 'h-1'}`}
                          ></div>
                        ))}
                      </div>
                      <span className="text-xs text-emerald-400">LIVE</span>
                    </div>
                  )}
                  
                  {/* Main Voice Input Button */}
                  <button
                    onClick={isListening ? stopVoiceInput : startVoiceInput}
                    className={`px-4 py-2 rounded-md font-medium transition-all duration-200 flex items-center space-x-2 ${isListening 
                      ? 'bg-red-600 hover:bg-red-700 shadow-lg shadow-red-500/30' 
                      : 'bg-emerald-600 hover:bg-emerald-700 shadow-lg shadow-emerald-500/30 hover:scale-105'}`}
                  >
                    {isListening ? (
                      <>
                        <span className="text-lg">⏹️</span>
                        <span>Stop Listening</span>
                      </>
                    ) : (
                      <>
                        <span className="text-lg">🎤</span>
                        <span>Voice Input</span>
                      </>
                    )}
                  </button>
                  
                  {/* Status Indicator */}
                  <div className="flex items-center space-x-2">
                    <div className={`w-3 h-3 rounded-full ${isListening ? 'bg-green-500 animate-pulse' : 'bg-gray-500'}`}></div>
                    <span className="text-sm">{isListening ? 'Listening...' : 'Standby'}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Main Dashboard Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
              {/* Live Call Panel */}
              <div className="lg:col-span-1">
                <div 
                  className={currentCall ? 'cursor-pointer hover:opacity-90 transition-opacity' : ''}
                  onClick={() => currentCall && showCallDetails(currentCall)}
                >
                  <CallPanel callData={currentCall} />
                  {currentCall && (
                    <div className="mt-2 text-center text-xs text-gray-500 flex items-center justify-center">
                      <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                      </svg>
                      Click to view details
                    </div>
                  )}
                </div>
              </div>

              {/* Summary Panel */}
              <div className="lg:col-span-1">
                <SummaryPanel callData={currentCall} />
              </div>

              {/* Map Panel */}
              <div className="lg:col-span-1">
                <MapPanel currentCall={currentCall} callHistory={callHistory} />
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
                  <div 
                    key={index} 
                    className="bg-gray-700 p-4 rounded-lg cursor-pointer hover:bg-gray-600 transition-colors"
                    onClick={() => showCallDetails(log)}
                  >
                    <div className="flex justify-between items-start">
                      <div>
                        <h3 className="font-medium">{log.predicted_class || log.emergency_type} - {log.severity}</h3>
                        <p className="text-sm text-gray-400">{new Date(log.timestamp).toLocaleString()}</p>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className={`px-2 py-1 rounded text-xs ${
                          log.severity === 'CRITICAL' ? 'bg-red-900 text-red-200' :
                          log.severity === 'HIGH' ? 'bg-orange-900 text-orange-200' :
                          log.severity === 'MEDIUM' ? 'bg-yellow-900 text-yellow-200' :
                          'bg-green-900 text-green-200'
                        }`}>
                          {log.severity}
                        </span>
                        <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                        </svg>
                      </div>
                    </div>
                    <p className="mt-2 text-sm">{log.transcript || log.input_text || 'No transcript available'}</p>
                    <div className="mt-2 flex justify-between text-xs text-gray-400">
                      <span>Routing: {log.routing_decision?.department || 'Unknown'}</span>
                      <span>Conf: {log.confidence ? (log.confidence * 100).toFixed(1) : 'N/A'}%</span>
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
      
      {/* Call Detail Modal */}
      <CallDetailModal 
        call={selectedCall} 
        onClose={closeCallDetails} 
      />
    </div>
  );
};

export default App;