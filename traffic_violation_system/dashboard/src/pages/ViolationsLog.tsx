import React, { useEffect, useState } from 'react';
import { FileText, Search, Image as ImageIcon } from 'lucide-react';
import './ViolationsLog.css';

interface Violation {
  timestamp: string;
  type: string;
  vehicle: string;
  confidence: string;
  bbox_x1: string;
  bbox_y1: string;
  bbox_x2: string;
  bbox_y2: string;
  image_file: string;
  message: string;
}

const ViolationsLog: React.FC = () => {
  const [violations, setViolations] = useState<Violation[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('ALL');

  useEffect(() => {
    const fetchViolations = async () => {
      try {
        const response = await fetch('https://perpetual-tug-theater.ngrok-free.dev/api/violations?limit=100');
        const data = await response.json();
        setViolations(data);
      } catch (error) {
        console.error("Failed to fetch violations:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchViolations();
    const interval = setInterval(fetchViolations, 10000); // Poll every 10 seconds
    return () => clearInterval(interval);
  }, []);

  const filteredViolations = violations.filter(v => filter === 'ALL' || v.type === filter);

  const formatDate = (isoString: string) => {
    const date = new Date(isoString);
    return new Intl.DateTimeFormat('en-US', {
      month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit'
    }).format(date);
  };

  return (
    <div className="violations-page animate-fade-in">
      <header className="page-header">
        <div>
          <h1 className="page-title">Violations Log</h1>
          <p className="page-subtitle">Detailed record of detected traffic offenses.</p>
        </div>
      </header>

      <div className="glass-card table-container">
        <div className="table-header-controls">
          <div className="search-bar">
            <Search size={18} className="search-icon" />
            <input type="text" placeholder="Search logs..." className="search-input" />
          </div>
          <div className="filter-group">
            <button className={`filter-btn ${filter === 'ALL' ? 'active' : ''}`} onClick={() => setFilter('ALL')}>All</button>
            <button className={`filter-btn ${filter === 'RED_LIGHT' ? 'active' : ''}`} onClick={() => setFilter('RED_LIGHT')}>Red Light</button>
            <button className={`filter-btn ${filter === 'NO_HELMET' ? 'active' : ''}`} onClick={() => setFilter('NO_HELMET')}>No Helmet</button>
          </div>
        </div>

        {loading ? (
          <div className="loading-state">
            <div className="spinner"></div>
            <p>Loading records...</p>
          </div>
        ) : (
          <div className="table-responsive">
            <table className="violations-table">
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Violation Type</th>
                  <th>Confidence</th>
                  <th>Evidence</th>
                </tr>
              </thead>
              <tbody>
                {filteredViolations.length > 0 ? (
                  filteredViolations.map((v, i) => (
                    <tr key={i}>
                      <td>{formatDate(v.timestamp)}</td>
                      <td>
                        <span className={`badge ${v.type === 'RED_LIGHT' ? 'badge-danger' : 'badge-warning'}`}>
                          {v.type.replace('_', ' ')}
                        </span>
                      </td>
                      <td>{(parseFloat(v.confidence) * 100).toFixed(1)}%</td>
                      <td>
                        <div className="evidence-cell">
                          {v.image_file ? (
                            <img 
                              src={`https://perpetual-tug-theater.ngrok-free.dev/api/images/${v.image_file}`} 
                              alt="Evidence" 
                              className="evidence-thumb" 
                            />
                          ) : (
                            <div className="no-evidence"><ImageIcon size={16} /></div>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={4} className="empty-state">
                      <FileText size={32} className="empty-icon" />
                      <p>No violations recorded yet.</p>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default ViolationsLog;
