import React, { useEffect, useState, useCallback } from 'react';
import StatCard from '../components/StatCard';
import { Camera, AlertCircle, ShieldAlert, CheckCircle2, RefreshCw, WifiOff, Wifi, MapPin } from 'lucide-react';
import './Overview.css';

interface SystemStats {
  total_violations: number;
  by_type: {
    RED_LIGHT?: number;
    NO_HELMET?: number;
  };
}

interface CameraStatus {
  connected: boolean;
  last_frame_time: number;
  frame_count: number;
  error: string | null;
  source: string;
  seconds_since_last_frame: number | null;
}

const Overview: React.FC = () => {
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [cameraStatus, setCameraStatus] = useState<CameraStatus | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [feedKey, setFeedKey] = useState(0); // Key to force img remount
  const [availableLocations, setAvailableLocations] = useState<Record<string, any>>({});
  const [currentLocationKey, setCurrentLocationKey] = useState<string>('demo');

  useEffect(() => {
    // Fetch stats from Flask backend
    const fetchStats = async () => {
      try {
        const response = await fetch('https://perpetual-tug-theater.ngrok-free.dev/api/stats', {
          headers: { 'ngrok-skip-browser-warning': 'true' }
        });
        const data = await response.json();
        setStats(data);
      } catch (error) {
        console.error("Failed to fetch stats:", error);
      }
    };

    fetchStats();
    const interval = setInterval(fetchStats, 5000); // Poll every 5 seconds
    return () => clearInterval(interval);
  }, []);

  // Fetch initial config for locations
  useEffect(() => {
    const fetchConfig = async () => {
      try {
        const response = await fetch('https://perpetual-tug-theater.ngrok-free.dev/api/config', {
          headers: { 'ngrok-skip-browser-warning': 'true' }
        });
        const data = await response.json();
        if (data.available_locations) {
          setAvailableLocations(data.available_locations);
        }
        
        if (data.source) {
          let matchedKey = data.source;
          if (data.source === 'demo' || data.source === '0') {
            matchedKey = data.source;
          } else {
            for (const [key, loc] of Object.entries(data.available_locations || {})) {
              if ((loc as any).source === data.source) {
                matchedKey = key;
                break;
              }
            }
          }
          setCurrentLocationKey(matchedKey);
        }
      } catch (error) {
        console.error("Failed to fetch config:", error);
      }
    };
    fetchConfig();
  }, []);

  useEffect(() => {
    // Poll camera status every 3 seconds
    const fetchCameraStatus = async () => {
      try {
        const response = await fetch('https://perpetual-tug-theater.ngrok-free.dev/api/camera_status', {
          headers: { 'ngrok-skip-browser-warning': 'true' }
        });
        const data = await response.json();
        setCameraStatus(data);
      } catch (error) {
        console.error("Failed to fetch camera status:", error);
      }
    };

    fetchCameraStatus();
    const interval = setInterval(fetchCameraStatus, 3000);
    return () => clearInterval(interval);
  }, []);

  const handleRefresh = useCallback(async () => {
    setRefreshing(true);
    try {
      await fetch('https://perpetual-tug-theater.ngrok-free.dev/api/refresh_camera', {
        method: 'POST',
        headers: { 'ngrok-skip-browser-warning': 'true' }
      });
      // Force the img element to remount by changing key (re-establishes MJPEG stream)
      setFeedKey(prev => prev + 1);
    } catch (error) {
      console.error("Failed to refresh camera:", error);
    } finally {
      setTimeout(() => setRefreshing(false), 2000);
    }
  }, []);

  const handleLocationChange = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    const key = e.target.value;
    setCurrentLocationKey(key);
    
    let finalSource = key;
    let finalLocationName = 'Mode Demo';
    
    if (availableLocations[key]) {
      finalSource = availableLocations[key].source;
      finalLocationName = availableLocations[key].name;
    } else if (key === '0') {
      finalLocationName = 'Local Webcam';
    } else if (key === 'demo') {
      finalLocationName = 'Mode Demo';
    }
    
    try {
      await fetch('https://perpetual-tug-theater.ngrok-free.dev/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'ngrok-skip-browser-warning': 'true' },
        body: JSON.stringify({ 
          source: finalSource,
          location_name: finalLocationName
        })
      });
      // Beri waktu sebentar agar backend memproses sebelum refresh stream
      setTimeout(handleRefresh, 500); 
    } catch (error) {
      console.error("Failed to update location:", error);
    }
  };

  const isStreamHealthy = cameraStatus?.connected && 
    (cameraStatus.seconds_since_last_frame === null || cameraStatus.seconds_since_last_frame < 5);

  return (
    <div className="overview-page animate-fade-in">
      <header className="page-header">
        <div>
          <h1 className="page-title">Dashboard Overview</h1>
          <p className="page-subtitle">Real-time traffic monitoring system status.</p>
        </div>
      </header>

      <div className="dashboard-grid">
        {/* Top Stats Row */}
        <div className="col-span-3">
          <StatCard 
            title="Total Violations" 
            value={stats?.total_violations || 0} 
            icon={<AlertCircle size={20} />} 
            colorClass="accent-amber"
          />
        </div>
        <div className="col-span-3">
          <StatCard 
            title="Red Light Running" 
            value={stats?.by_type?.RED_LIGHT || 0} 
            icon={<ShieldAlert size={20} />} 
            colorClass="accent-red"
          />
        </div>
        <div className="col-span-3">
          <StatCard 
            title="No Helmet Detected" 
            value={stats?.by_type?.NO_HELMET || 0} 
            icon={<ShieldAlert size={20} />} 
            colorClass="accent-amber"
          />
        </div>
        <div className="col-span-3">
          <StatCard 
            title="Active Cameras" 
            value="1" 
            icon={<Camera size={20} />} 
            colorClass="accent-green"
          />
        </div>

        {/* Live Feed Section */}
        <div className="col-span-8 live-feed-container glass-card">
          <div className="section-header">
            <h3>Live Camera Feed</h3>
            <div className="feed-header-actions">
              {/* Camera status indicator */}
              <div className={`badge ${isStreamHealthy ? 'badge-success' : 'badge-danger'}`}>
                {isStreamHealthy ? (
                  <><Wifi size={12} /><span className="dot"></span> LIVE</>
                ) : (
                  <><WifiOff size={12} /> DISCONNECTED</>
                )}
              </div>
              {/* Refresh button */}
              <button 
                id="refresh-camera-btn"
                className={`btn-refresh ${refreshing ? 'spinning' : ''}`} 
                onClick={handleRefresh} 
                disabled={refreshing}
                title="Refresh camera connection"
              >
                <RefreshCw size={16} />
                {refreshing ? 'Reconnecting...' : 'Refresh'}
              </button>
            </div>
          </div>

          {/* Camera error banner */}
          {cameraStatus?.error && (
            <div className="camera-error-banner animate-fade-in">
              <AlertCircle size={16} />
              <span>{cameraStatus.error}</span>
            </div>
          )}

          <div className="video-wrapper">
            <img 
              key={feedKey}
              src={`https://perpetual-tug-theater.ngrok-free.dev/api/video_feed?t=${feedKey}`}
              alt="Live Traffic Feed" 
              className="live-video-feed" 
              onError={(e) => {
                e.currentTarget.style.display = 'none';
                e.currentTarget.parentElement!.classList.add('video-error');
              }}
              onLoad={(e) => {
                e.currentTarget.style.display = 'block';
                e.currentTarget.parentElement!.classList.remove('video-error');
              }}
            />
            <div className="video-overlay">
              <Camera size={48} className="overlay-icon" />
              <p>Connecting to camera feed...</p>
            </div>
          </div>

          {/* Camera info bar */}
          {cameraStatus && (
            <div className="camera-info-bar">
              <span className="camera-info-item">
                Source: <strong>{cameraStatus.source}</strong>
              </span>
              <span className="camera-info-item">
                Frames: <strong>{cameraStatus.frame_count.toLocaleString()}</strong>
              </span>
              {cameraStatus.seconds_since_last_frame !== null && (
                <span className="camera-info-item">
                  Last frame: <strong>{cameraStatus.seconds_since_last_frame}s ago</strong>
                </span>
              )}
            </div>
          )}
        </div>

        {/* System Status / Quick Logs */}
        <div className="col-span-4 system-status-container glass-card">
          <div className="section-header">
            <h3>System Status</h3>
          </div>
          <div className="status-list">
            
            {/* LOCATION SELECTOR */}
            <div className="status-item" style={{ alignItems: 'flex-start' }}>
              <MapPin className="text-blue-400" size={18} style={{ marginTop: '2px' }} />
              <div className="status-info" style={{ width: '100%' }}>
                <p className="status-name" style={{ marginBottom: '6px' }}>Active Location</p>
                <select 
                  value={currentLocationKey}
                  onChange={handleLocationChange}
                  className="location-dropdown"
                  style={{ 
                    width: '100%', 
                    padding: '6px 8px', 
                    borderRadius: '6px',
                    background: 'rgba(15, 23, 42, 0.6)',
                    color: '#e2e8f0',
                    border: '1px solid rgba(148, 163, 184, 0.2)',
                    fontSize: '0.85rem',
                    outline: 'none',
                    cursor: 'pointer'
                  }}
                >
                  <option value="demo" style={{ color: 'black' }}>Mode Demo</option>
                  <option value="0" style={{ color: 'black' }}>Local Webcam</option>
                  {Object.entries(availableLocations).map(([k, loc]) => (
                    <option key={k} value={k} style={{ color: 'black' }}>{loc.name}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="status-item">
              {isStreamHealthy ? (
                <CheckCircle2 className="text-green-500" size={18} />
              ) : (
                <AlertCircle className="text-red-500" size={18} />
              )}
              <div className="status-info">
                <p className="status-name">Camera Feed</p>
                <p className="status-desc">
                  {isStreamHealthy ? `Connected — ${cameraStatus?.source}` : 'Disconnected'}
                </p>
              </div>
            </div>
            <div className="status-item">
              <CheckCircle2 className="text-green-500" size={18} />
              <div className="status-info">
                <p className="status-name">Detection Model</p>
                <p className="status-desc">YOLOv8n Active (30 FPS)</p>
              </div>
            </div>
            <div className="status-item">
              <CheckCircle2 className="text-green-500" size={18} />
              <div className="status-info">
                <p className="status-name">Database Link</p>
                <p className="status-desc">Connected (CSV Log)</p>
              </div>
            </div>
            <div className="status-item">
              <CheckCircle2 className="text-green-500" size={18} />
              <div className="status-info">
                <p className="status-name">Traffic Light Monitor</p>
                <p className="status-desc">Simulated Mode</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Overview;
