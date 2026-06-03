import React, { useState, useEffect } from 'react';
import { Camera, Save, CheckCircle } from 'lucide-react';
import './Settings.css';

const Settings: React.FC = () => {
  const [source, setSource] = useState('demo');
  const [customSource, setCustomSource] = useState('');
  const [locationName, setLocationName] = useState('Mode Demo');
  const [availableLocations, setAvailableLocations] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    const fetchConfig = async () => {
      try {
        const response = await fetch('https://perpetual-tug-theater.ngrok-free.dev/api/config');
        const data = await response.json();
        if (data.available_locations) {
          setAvailableLocations(data.available_locations);
        }
        
        if (data.source) {
          // Determine which radio to select
          let matchedKey = '';
          if (data.source === 'demo' || data.source === '0') {
            setSource(data.source);
            setLocationName(data.location_name || (data.source === 'demo' ? 'Mode Demo' : 'Local Webcam'));
          } else {
            // Check if it's one of our predefined locations
            for (const [key, loc] of Object.entries(data.available_locations || {})) {
              if ((loc as any).source === data.source) {
                matchedKey = key;
                break;
              }
            }
            
            if (matchedKey) {
              setSource(matchedKey); // Use the key as the radio value
              setLocationName(data.location_name || (data.available_locations[matchedKey] as any).name);
            } else {
              setSource('custom');
              setCustomSource(data.source);
              setLocationName(data.location_name || 'Custom Camera');
            }
          }
        }
      } catch (error) {
        console.error("Failed to fetch config:", error);
      }
    };
    fetchConfig();
  }, []);

  const handleSave = async () => {
    setLoading(true);
    
    let finalSource = source;
    let finalLocationName = locationName;

    if (source === 'custom') {
      finalSource = customSource;
      finalLocationName = 'Custom Camera';
    } else if (availableLocations[source]) {
      finalSource = availableLocations[source].source;
      finalLocationName = availableLocations[source].name;
    } else if (source === 'demo') {
      finalLocationName = 'Mode Demo';
    } else if (source === '0') {
      finalLocationName = 'Local Webcam';
    }
    
    try {
      await fetch('https://perpetual-tug-theater.ngrok-free.dev/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          source: finalSource,
          location_name: finalLocationName
        })
      });
      
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (error) {
      console.error("Failed to save config:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="settings-page animate-fade-in">
      <header className="page-header">
        <div>
          <h1 className="page-title">System Settings</h1>
          <p className="page-subtitle">Configure camera source and detection parameters.</p>
        </div>
      </header>

      <div className="dashboard-grid">
        <div className="col-span-8">
          <div className="glass-card settings-card">
            <div className="section-header">
              <h3><Camera size={20} className="inline-icon" /> Camera Configuration</h3>
            </div>
            
            <div className="settings-form">
              <div className="form-group">
                <label className="form-label">Video Source</label>
                <div className="radio-group">
                  <label className={`radio-card ${source === 'demo' ? 'selected' : ''}`}>
                    <input 
                      type="radio" 
                      name="camera-source" 
                      value="demo" 
                      checked={source === 'demo'} 
                      onChange={(e) => setSource(e.target.value)} 
                    />
                    <div className="radio-content">
                      <span className="radio-title">Demo Mode</span>
                      <span className="radio-desc">Simulated synthetic traffic video</span>
                    </div>
                  </label>
                  
                  <label className={`radio-card ${source === '0' ? 'selected' : ''}`}>
                    <input 
                      type="radio" 
                      name="camera-source" 
                      value="0" 
                      checked={source === '0'} 
                      onChange={(e) => setSource(e.target.value)} 
                    />
                    <div className="radio-content">
                      <span className="radio-title">Local Webcam</span>
                      <span className="radio-desc">Primary system camera (Index 0)</span>
                    </div>
                  </label>
                  

                  
                  <label className={`radio-card ${source === 'custom' ? 'selected' : ''}`}>
                    <input 
                      type="radio" 
                      name="camera-source" 
                      value="custom" 
                      checked={source === 'custom'} 
                      onChange={(e) => setSource(e.target.value)} 
                    />
                    <div className="radio-content">
                      <span className="radio-title">RTSP / Video File</span>
                      <span className="radio-desc">Custom network stream or file path</span>
                    </div>
                  </label>
                </div>
              </div>

              {source === 'custom' && (
                <div className="form-group animate-fade-in">
                  <label className="form-label">Custom Source URL/Path</label>
                  <input 
                    type="text" 
                    className="form-input" 
                    placeholder="e.g. rtsp://192.168.1.100/stream" 
                    value={customSource}
                    onChange={(e) => setCustomSource(e.target.value)}
                  />
                </div>
              )}
              
              <div className="form-actions">
                <button 
                  className={`btn-primary ${saved ? 'btn-success' : ''}`} 
                  onClick={handleSave}
                  disabled={loading}
                >
                  {loading ? (
                    <span>Saving...</span>
                  ) : saved ? (
                    <><CheckCircle size={18} /> Saved successfully</>
                  ) : (
                    <><Save size={18} /> Save Settings</>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;
