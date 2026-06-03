import React from 'react';
import './StatCard.css';

interface StatCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  trend?: {
    value: string;
    isPositive: boolean;
  };
  colorClass?: string;
}

const StatCard: React.FC<StatCardProps> = ({ title, value, icon, trend, colorClass = 'accent-blue' }) => {
  return (
    <div className={`stat-card glass-card ${colorClass}`}>
      <div className="stat-card-header">
        <h3 className="stat-title">{title}</h3>
        <div className="stat-icon-wrapper">
          {icon}
        </div>
      </div>
      
      <div className="stat-content">
        <div className="stat-value">{value}</div>
        
        {trend && (
          <div className={`stat-trend ${trend.isPositive ? 'positive' : 'negative'}`}>
            <span className="trend-icon">
              {trend.isPositive ? '↑' : '↓'}
            </span>
            <span className="trend-value">{trend.value}</span>
            <span className="trend-label">vs last period</span>
          </div>
        )}
      </div>
    </div>
  );
};

export default StatCard;
