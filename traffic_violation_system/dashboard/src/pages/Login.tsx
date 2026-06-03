import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Activity, Mail, Lock, LogIn, AlertCircle } from 'lucide-react';
import './Login.css';

interface LoginProps {
  onLogin: () => void;
}

const Login: React.FC<LoginProps> = ({ onLogin }) => {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    // Mock Authentication Logic
    setTimeout(async () => {
      setIsLoading(false);
      // For demonstration, accept any non-empty credentials
      if (email && password) {
        
        // Reset backend to demo mode on fresh login
        try {
          await fetch('https://perpetual-tug-theater.ngrok-free.dev/api/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'ngrok-skip-browser-warning': 'true' },
            body: JSON.stringify({ 
              source: 'demo',
              location_name: 'Mode Demo'
            })
          });
          // Call refresh_camera to force stream update
          await fetch('https://perpetual-tug-theater.ngrok-free.dev/api/refresh_camera', {
            method: 'POST',
            headers: { 'ngrok-skip-browser-warning': 'true' }
          });
        } catch (error) {
          console.error("Failed to reset location:", error);
        }

        onLogin();
        navigate('/dashboard');
      } else {
        setError('Please enter both email and password.');
      }
    }, 1000);
  };

  return (
    <div className="login-page animate-fade-in">
      <div className="login-container glass-card">
        <div className="login-header">
          <div className="logo-container justify-center mb-4">
            <Activity className="logo-icon" size={32} />
          </div>
          <h1 className="login-title">Welcome Back</h1>
          <p className="login-subtitle">Sign in to TrafficGuard Dashboard</p>
        </div>

        {error && (
          <div className="login-error animate-fade-in">
            <AlertCircle size={16} />
            <span>{error}</span>
          </div>
        )}

        <form className="login-form" onSubmit={handleLogin}>
          <div className="form-group">
            <label className="form-label">Email Address</label>
            <div className="input-with-icon">
              <Mail className="input-icon" size={18} />
              <input
                type="email"
                className="form-input has-icon"
                placeholder="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Password</label>
            <div className="input-with-icon">
              <Lock className="input-icon" size={18} />
              <input
                type="password"
                className="form-input has-icon"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
          </div>

          <button
            type="submit"
            className="btn-primary login-btn"
            disabled={isLoading}
          >
            {isLoading ? (
              <span className="spinner"></span>
            ) : (
              <><LogIn size={18} /> Sign In</>
            )}
          </button>
        </form>

        <div className="login-footer">
          <p>Secure connection. All activities are monitored.</p>
        </div>
      </div>
    </div>
  );
};

export default Login;
