'use client';

import React from 'react';

interface AgentFrameworkLogoProps {
  size?: number;
  className?: string;
}

const AgentFrameworkLogo: React.FC<AgentFrameworkLogoProps> = ({ size = 32, className = "" }) => {
  return (
    <div className={`inline-block ${className}`} style={{ width: size, height: size }}>
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" className="w-full h-full">
        {/* Background */}
        <rect width="32" height="32" fill="#2B4255"/>
        
        {/* Main circle */}
        <circle cx="16" cy="16" r="14" fill="none" stroke="#888" strokeWidth="2"/>
        
        {/* Center circle */}
        <circle cx="16" cy="16" r="4" fill="none" stroke="#888" strokeWidth="1.5"/>
        
        {/* Blue dot */}
        <circle cx="16" cy="16" r="1.5" fill="#2B9FFF"/>
        
        {/* Nodes and spokes */}
        <g>
          {/* Vertical nodes */}
          <line x1="16" y1="12" x2="16" y2="8" stroke="#888" strokeWidth="1.5"/>
          <circle cx="16" cy="6" r="1.5" fill="none" stroke="#2B9FFF" strokeWidth="1"/>
          
          <line x1="16" y1="20" x2="16" y2="24" stroke="#888" strokeWidth="1.5"/>
          <circle cx="16" cy="26" r="1.5" fill="none" stroke="#2B9FFF" strokeWidth="1"/>
          
          {/* Horizontal nodes */}
          <line x1="20" y1="16" x2="24" y2="16" stroke="#888" strokeWidth="1.5"/>
          <circle cx="26" cy="16" r="1.5" fill="none" stroke="#2B9FFF" strokeWidth="1"/>
          
          <line x1="12" y1="16" x2="8" y2="16" stroke="#888" strokeWidth="1.5"/>
          <circle cx="6" cy="16" r="1.5" fill="none" stroke="#2B9FFF" strokeWidth="1"/>
          
          {/* Diagonal nodes */}
          <line x1="19" y1="13" x2="22" y2="10" stroke="#888" strokeWidth="1.5"/>
          <circle cx="23.5" cy="8.5" r="1.5" fill="none" stroke="#2B9FFF" strokeWidth="1"/>
          
          <line x1="19" y1="19" x2="22" y2="22" stroke="#888" strokeWidth="1.5"/>
          <circle cx="23.5" cy="23.5" r="1.5" fill="none" stroke="#2B9FFF" strokeWidth="1"/>
          
          <line x1="13" y1="19" x2="10" y2="22" stroke="#888" strokeWidth="1.5"/>
          <circle cx="8.5" cy="23.5" r="1.5" fill="none" stroke="#2B9FFF" strokeWidth="1"/>
          
          <line x1="13" y1="13" x2="10" y2="10" stroke="#888" strokeWidth="1.5"/>
          <circle cx="8.5" cy="8.5" r="1.5" fill="none" stroke="#2B9FFF" strokeWidth="1"/>
        </g>
      </svg>
    </div>
  );
};

export default AgentFrameworkLogo;
