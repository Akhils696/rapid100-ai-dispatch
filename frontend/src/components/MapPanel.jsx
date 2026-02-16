import React, { useEffect, useRef, useState } from 'react';
import axios from 'axios';

const MapPanel = ({ currentCall, callHistory }) => {
  const mapRef = useRef(null);
  const mapInstance = useRef(null);
  const markersRef = useRef([]);
  const [mapLoaded, setMapLoaded] = useState(false);

  // Initialize map when component mounts
  useEffect(() => {
    if (mapRef.current && !mapLoaded) {
      // Check if Google Maps is already loaded
      if (window.google && window.google.maps) {
        initializeMap();
        return;
      }
      
      // Load Google Maps API
      const script = document.createElement('script');
      script.src = `https://maps.googleapis.com/maps/api/js?key=AIzaSyDPhKi-iT-76-42dIQjg4KO4v2MDB99e18&callback=initMap`;
      script.async = true;
      script.defer = true;
      
      // Global callback function for map initialization
      window.initMap = () => {
        initializeMap();
      };

      // Error handling
      script.onerror = () => {
        console.error('Failed to load Google Maps API');
        setShowFallback(true);
      };

      document.head.appendChild(script);

      return () => {
        if (window.initMap) {
          delete window.initMap;
        }
      };
    }
  }, []);

  const initializeMap = () => {
    try {
      const mapOptions = {
        center: { lat: 40.7128, lng: -74.0060 }, // New York default
        zoom: 12,
        mapTypeId: 'roadmap',
        styles: [
          {
            featureType: 'administrative',
            elementType: 'labels',
            stylers: [{ visibility: 'on' }]
          },
          {
            featureType: 'poi',
            elementType: 'labels',
            stylers: [{ visibility: 'off' }]
          }
        ]
      };

      mapInstance.current = new window.google.maps.Map(mapRef.current, mapOptions);
      setMapLoaded(true);
      setShowFallback(false);
      
      // Add emergency markers
      updateMapMarkers();
    } catch (error) {
      console.error('Error initializing map:', error);
      setShowFallback(true);
    }
  };

  const [showFallback, setShowFallback] = useState(false);

  // Update markers when call data changes
  useEffect(() => {
    if (mapLoaded && mapInstance.current) {
      updateMapMarkers();
    }
  }, [currentCall, callHistory, mapLoaded]);

  const updateMapMarkers = () => {
    // Clear existing markers
    markersRef.current.forEach(marker => marker.setMap(null));
    markersRef.current = [];

    // Combine current call and history for display
    const allCalls = [];
    if (currentCall) {
      allCalls.push(currentCall);
    }
    allCalls.push(...callHistory.slice(0, 20)); // Show last 20 calls

    // Add markers for each call with location data
    allCalls.forEach((call, index) => {
      if (call.location_data && call.location_data.latitude && call.location_data.longitude) {
        const position = {
          lat: parseFloat(call.location_data.latitude),
          lng: parseFloat(call.location_data.longitude)
        };

        // Determine marker color based on severity
        const getMarkerColor = (severity) => {
          switch (severity) {
            case 'CRITICAL': return '#FF0000'; // Red
            case 'HIGH': return '#FF8C00';     // Dark Orange
            case 'MEDIUM': return '#FFD700';   // Gold
            case 'LOW': return '#32CD32';      // Green
            default: return '#808080';         // Gray
          }
        };

        // Create marker
        const marker = new window.google.maps.Marker({
          position: position,
          map: mapInstance.current,
          title: `${call.emergency_type} - ${call.severity}`,
          icon: {
            path: window.google.maps.SymbolPath.CIRCLE,
            fillColor: getMarkerColor(call.severity),
            fillOpacity: 0.8,
            strokeColor: '#000000',
            strokeWeight: 2,
            scale: 12
          }
        });

        // Add info window
        const infoWindow = new window.google.maps.InfoWindow({
          content: `
            <div style="padding: 10px; max-width: 200px;">
              <h3 style="margin: 0 0 8px 0; color: ${getMarkerColor(call.severity)}">
                ${call.emergency_type}
              </h3>
              <p style="margin: 4px 0; font-weight: bold;">Severity: ${call.severity}</p>
              <p style="margin: 4px 0;">Location: ${call.location || 'Unknown'}</p>
              ${call.transcript ? `<p style="margin: 4px 0; font-size: 12px;">${call.transcript.substring(0, 100)}...</p>` : ''}
              <p style="margin: 4px 0; font-size: 11px; color: #666;">
                ${new Date(call.timestamp).toLocaleString()}
              </p>
            </div>
          `
        });

        // Add click event
        marker.addListener('click', () => {
          infoWindow.open(mapInstance.current, marker);
        });

        markersRef.current.push(marker);
      }
    });

    // Fit map to show all markers
    if (markersRef.current.length > 0) {
      const bounds = new window.google.maps.LatLngBounds();
      markersRef.current.forEach(marker => {
        bounds.extend(marker.getPosition());
      });
      mapInstance.current.fitBounds(bounds);
    }
  };

  const getSeverityStats = () => {
    const allCalls = currentCall ? [currentCall, ...callHistory] : [...callHistory];
    const stats = {
      CRITICAL: 0,
      HIGH: 0,
      MEDIUM: 0,
      LOW: 0
    };

    allCalls.forEach(call => {
      if (stats.hasOwnProperty(call.severity)) {
        stats[call.severity]++;
      }
    });

    return stats;
  };

  const severityStats = getSeverityStats();

  // Fallback map visualization
  const renderFallbackMap = () => {
    const allCalls = currentCall ? [currentCall, ...callHistory] : [...callHistory];
    const callsWithLocation = allCalls.filter(call => 
      call.location_data && call.location_data.latitude && call.location_data.longitude
    );
    
    return (
      <div className="w-full h-full bg-gray-900 rounded-b-lg flex items-center justify-center relative">
        <div className="text-center p-4">
          <div className="mb-4">
            <div className="text-4xl mb-2">🗺️</div>
            <h3 className="text-lg font-semibold text-white mb-2">Emergency Locations</h3>
            <p className="text-gray-400 text-sm mb-4">
              {callsWithLocation.length > 0 
                ? `${callsWithLocation.length} emergency locations` 
                : 'No location data available'
              }
            </p>
          </div>
          
          {/* Simple coordinate visualization */}
          <div className="bg-gray-800 rounded-lg p-4 max-w-md">
            <h4 className="text-gray-300 font-medium mb-3">Recent Locations:</h4>
            <div className="space-y-2 max-h-40 overflow-y-auto">
              {callsWithLocation.slice(0, 5).map((call, index) => (
                <div key={index} className="flex items-center text-sm">
                  <div className={`w-3 h-3 rounded-full mr-2 ${
                    call.severity === 'CRITICAL' ? 'bg-red-500' :
                    call.severity === 'HIGH' ? 'bg-orange-500' :
                    call.severity === 'MEDIUM' ? 'bg-yellow-500' :
                    'bg-green-500'
                  }`}></div>
                  <div className="text-left">
                    <div className="text-white font-medium">{call.emergency_type}</div>
                    <div className="text-gray-400">
                      {call.location_data.area || 'Unknown Area'}
                    </div>
                    <div className="text-gray-500 text-xs">
                      {call.location_data.latitude.toFixed(4)}, {call.location_data.longitude.toFixed(4)}
                    </div>
                  </div>
                </div>
              ))}
              {callsWithLocation.length === 0 && (
                <div className="text-gray-500 text-sm py-4">
                  No emergency locations to display
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="bg-gray-800 rounded-lg shadow-lg h-full flex flex-col">
      <div className="p-4 border-b border-gray-700">
        <h2 className="text-lg font-semibold text-white flex items-center">
          <span className="mr-2">🗺️</span>
          Emergency Map
        </h2>
        <p className="text-sm text-gray-400 mt-1">
          Real-time emergency locations and severity distribution
        </p>
        {showFallback && (
          <div className="mt-2 p-2 bg-yellow-900 bg-opacity-30 rounded text-yellow-200 text-xs">
            Google Maps API not available. Showing fallback visualization.
          </div>
        )}
      </div>
      
      <div className="flex-1 relative">
        {!mapLoaded && !showFallback && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-900">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emergency-red mx-auto mb-4"></div>
              <p className="text-gray-400">Loading map...</p>
            </div>
          </div>
        )}
        {showFallback ? (
          renderFallbackMap()
        ) : (
          <div 
            ref={mapRef} 
            className="w-full h-full rounded-b-lg"
            style={{ minHeight: '400px' }}
          />
        )}
      </div>
      
      {/* Severity Legend */}
      <div className="p-4 border-t border-gray-700">
        <h3 className="text-sm font-medium text-gray-300 mb-3">Severity Distribution</h3>
        <div className="grid grid-cols-2 gap-3">
          <div className="flex items-center">
            <div className="w-3 h-3 bg-red-500 rounded-full mr-2"></div>
            <span className="text-xs text-gray-400">Critical: {severityStats.CRITICAL}</span>
          </div>
          <div className="flex items-center">
            <div className="w-3 h-3 bg-orange-500 rounded-full mr-2"></div>
            <span className="text-xs text-gray-400">High: {severityStats.HIGH}</span>
          </div>
          <div className="flex items-center">
            <div className="w-3 h-3 bg-yellow-500 rounded-full mr-2"></div>
            <span className="text-xs text-gray-400">Medium: {severityStats.MEDIUM}</span>
          </div>
          <div className="flex items-center">
            <div className="w-3 h-3 bg-green-500 rounded-full mr-2"></div>
            <span className="text-xs text-gray-400">Low: {severityStats.LOW}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MapPanel;