import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Video, AlertTriangle, Settings, Activity, LogOut } from 'lucide-react';
import './Sidebar.css';

interface SidebarProps {
  onLogout?: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({ onLogout }) => {
  return (
    <aside className="sidebar glass-card">
      <div className="sidebar-header">
        <div className="logo-container">
          <Activity className="logo-icon" size={28} />
          <h2 className="logo-text">TrafficGuard</h2>
        </div>
      </div>
      
      <nav className="sidebar-nav">
        <div className="nav-section">
          <p className="nav-section-title">MAIN</p>
          <NavLink to="/dashboard" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`} end>
            <LayoutDashboard size={20} />
            <span>Overview</span>
          </NavLink>
          <NavLink to="/dashboard/live" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <Video size={20} />
            <span>Live Feed</span>
          </NavLink>
          <NavLink to="/dashboard/violations" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <AlertTriangle size={20} />
            <span>Violations Log</span>
          </NavLink>
        </div>
        
        <div className="nav-section">
          <p className="nav-section-title">SYSTEM</p>
          <NavLink to="/dashboard/settings" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <Settings size={20} />
            <span>Settings</span>
          </NavLink>
        </div>
      </nav>
      
      <div className="sidebar-footer">
        {onLogout && (
          <button 
            onClick={onLogout}
            className="nav-item" 
            style={{ width: '100%', background: 'transparent', border: 'none', cursor: 'pointer', textAlign: 'left', marginBottom: '1rem', color: '#ef4444' }}
          >
            <LogOut size={20} />
            <span>Sign Out</span>
          </button>
        )}
        <div className="system-status">
          <div className="status-indicator online"></div>
          <span>System Online</span>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
