import React from 'react';
import './RoleSelection.css';

export default function RoleSelection({ onSelectRole }) {
  return (
    <div className="role-selection-wrapper">
      <div className="role-selection-content">
        <h1 className="gradient-text title">ProCareer Platform</h1>
        <p className="subtitle">Select your role to access the platform</p>
        
        <div className="role-buttons">
          <button 
            className="role-btn hr-btn" 
            onClick={() => onSelectRole('HR')}
          >
            👨‍💼 Enter as HR
          </button>
          
          <button 
            className="role-btn student-btn" 
            onClick={() => onSelectRole('Student')}
          >
            🎓 Enter as Student
          </button>
        </div>
      </div>
    </div>
  );
}
