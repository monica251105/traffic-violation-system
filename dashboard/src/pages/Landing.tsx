import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Activity, ShieldCheck, Video, Zap, ArrowRight, Lock } from 'lucide-react';
import './Landing.css';

const Landing: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="landing-page animate-fade-in">
      <nav className="landing-nav glass-card">
        <div className="logo-container">
          <Activity className="logo-icon" size={28} />
          <h2 className="logo-text">TrafficGuard</h2>
        </div>
        <div className="nav-actions">
          <button className="btn-secondary" onClick={() => navigate('/login')}>
            <Lock size={16} /> Sign In
          </button>
        </div>
      </nav>

      <main className="landing-main">
        <section className="hero-section">
          <div className="hero-content">
            <div className="hero-badge">v2.0 Artificial Intelligence System</div>
            <h1 className="hero-title">
              Next-Gen <span className="text-gradient">Traffic Monitoring</span>
            </h1>
            <p className="hero-subtitle">
              Advanced AI-powered traffic violation detection system. Monitor red light running and helmet violations in real-time with unparalleled accuracy.
            </p>
            <div className="hero-cta">
              <button className="btn-primary btn-large" onClick={() => navigate('/login')}>
                Access Dashboard <ArrowRight size={20} />
              </button>
            </div>
          </div>
          <div className="hero-graphics">
            <div className="glass-card mockup-card">
              <div className="mockup-header">
                <div className="dots">
                  <span></span><span></span><span></span>
                </div>
                <div className="mockup-title">Live Detection Feed</div>
              </div>
              <div className="mockup-body">
                <div className="mockup-skeleton banner"></div>
                <div className="mockup-skeleton video-area">
                  <div className="detection-box"></div>
                  <div className="detection-label">RED LIGHT</div>
                </div>
                <div className="mockup-metrics">
                  <div className="mockup-skeleton stat"></div>
                  <div className="mockup-skeleton stat"></div>
                  <div className="mockup-skeleton stat"></div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="features-section">
          <h2 className="section-title">System Capabilities</h2>
          <div className="features-grid">
            <div className="feature-card glass-card">
              <div className="feature-icon"><Video size={24} /></div>
              <h3>Real-Time Processing</h3>
              <p>Process live camera feeds instantly with hardware-accelerated OpenCV integration.</p>
            </div>
            <div className="feature-card glass-card">
              <div className="feature-icon"><Zap size={24} /></div>
              <h3>YOLOv8 AI Detection</h3>
              <p>State-of-the-art neural networks for high-speed object and violation classification.</p>
            </div>
            <div className="feature-card glass-card">
              <div className="feature-icon"><ShieldCheck size={24} /></div>
              <h3>Automated Logging</h3>
              <p>Every violation is securely logged with snapshot evidence and exact timestamps.</p>
            </div>
          </div>
        </section>
      </main>

      <footer className="landing-footer glass-card">
        <p>&copy; 2026 TrafficGuard System. Secure Traffic Monitoring.</p>
      </footer>
    </div>
  );
};

export default Landing;
