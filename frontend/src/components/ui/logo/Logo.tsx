import React from 'react';

interface LogoProps {
  size?: number;
  className?: string;
}

export const Logo: React.FC<LogoProps> = ({ size = 40, className = '' }) => {
  return (
    <svg 
      width={size} 
      height={size} 
      viewBox="0 0 100 100" 
      fill="none" 
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-label="Agent Framework Logo"
    >
      <circle cx="50" cy="50" r="45" fill="currentColor" fillOpacity="0.1" />
      <path 
        d="M50 15C30.67 15 15 30.67 15 50C15 69.33 30.67 85 50 85C69.33 85 85 69.33 85 50C85 30.67 69.33 15 50 15ZM50 25C58.28 25 65 31.72 65 40C65 48.28 58.28 55 50 55C41.72 55 35 48.28 35 40C35 31.72 41.72 25 50 25ZM50 75C41.67 75 34.23 71.28 30 65.35C30.13 57.67 45 53.5 50 53.5C54.97 53.5 69.87 57.67 70 65.35C65.77 71.28 58.33 75 50 75Z"
        fill="currentColor"
      />
    </svg>
  );
};

export default Logo;