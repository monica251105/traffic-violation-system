import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Overview from './pages/Overview';
import ViolationsLog from './pages/ViolationsLog';
import Settings from './pages/Settings';
import Landing from './pages/Landing';
import Login from './pages/Login';
import './App.css';

const App: React.FC = () => {
  const [isAuthenticated, setIsAuthenticated] = React.useState(false);

  return (
    <Router>
      <Routes>
        {/* Public Routes */}
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login onLogin={() => setIsAuthenticated(true)} />} />

        {/* Protected Dashboard Routes */}
        <Route path="/dashboard/*" element={
          isAuthenticated ? (
            <div className="app-container">
              <Sidebar onLogout={() => setIsAuthenticated(false)} />
              <main className="main-content">
                <Routes>
                  <Route path="/" element={<Overview />} />
                  <Route path="/live" element={<Navigate to="/dashboard" replace />} />
                  <Route path="/violations" element={<ViolationsLog />} />
                  <Route path="/settings" element={<Settings />} />
                  <Route path="*" element={<Navigate to="/dashboard" replace />} />
                </Routes>
              </main>
            </div>
          ) : (
            <Navigate to="/" replace />
          )
        } />
        
        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
};

export default App;
