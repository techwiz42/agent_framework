import React from 'react';

interface RobotLogoProps {
  size?: number;
  className?: string;
}

export const RobotLogo: React.FC<RobotLogoProps> = ({ 
  size = 96, 
  className = "" 
}) => {
  return (
    <svg 
      width={size} 
      height={size} 
      viewBox="0 0 200 200" 
      fill="none" 
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-hidden="true"
    >
      {/* Frame */}
      <rect x="10" y="10" width="180" height="180" rx="20" fill="#EFF6FF" stroke="#3B82F6" strokeWidth="4" />
      
      {/* Robot Head */}
      <rect x="60" y="30" width="80" height="70" rx="10" fill="#3B82F6" />
      
      {/* Robot Eyes */}
      <circle cx="80" cy="55" r="10" fill="#EFF6FF" />
      <circle cx="120" cy="55" r="10" fill="#EFF6FF" />
      <circle cx="80" cy="55" r="5" fill="#1E40AF" />
      <circle cx="120" cy="55" r="5" fill="#1E40AF" />
      
      {/* Robot Mouth */}
      <rect x="75" y="75" width="50" height="10" rx="5" fill="#EFF6FF" />
      
      {/* Robot Antenna */}
      <rect x="95" y="15" width="10" height="15" fill="#3B82F6" />
      <circle cx="100" cy="15" r="7" fill="#EF4444" />
      
      {/* Robot Body */}
      <rect x="70" y="110" width="60" height="50" rx="5" fill="#3B82F6" />
      
      {/* Robot Neck */}
      <rect x="90" y="100" width="20" height="10" fill="#2563EB" />
      
      {/* Robot Arms */}
      <rect x="40" y="115" width="30" height="10" rx="5" fill="#2563EB" />
      <rect x="130" y="115" width="30" height="10" rx="5" fill="#2563EB" />
      
      {/* Robot Legs */}
      <rect x="80" y="160" width="10" height="25" rx="5" fill="#2563EB" />
      <rect x="110" y="160" width="10" height="25" rx="5" fill="#2563EB" />
      
      {/* Robot Control Panel */}
      <rect x="80" y="120" width="40" height="25" rx="3" fill="#1E40AF" />
      <circle cx="90" cy="130" r="3" fill="#EF4444" />
      <circle cx="100" cy="130" r="3" fill="#10B981" />
      <circle cx="110" cy="130" r="3" fill="#F59E0B" />
      <rect x="85" y="140" width="30" height="2" rx="1" fill="#EFF6FF" />
    </svg>
  );
};

export default RobotLogo;