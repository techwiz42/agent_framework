// src/components/ui/SimpleBadge.tsx
import React from 'react';

interface SimpleBadgeProps {
  children: React.ReactNode;
  variant?: 'default' | 'outline' | 'secondary';
  className?: string;
}

export const SimpleBadge: React.FC<SimpleBadgeProps> = ({ 
  children, 
  variant = 'default',
  className = '' 
}) => {
  const baseStyles = "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold";
  
  const variantStyles = {
    default: "bg-blue-100 text-blue-800",
    outline: "border border-gray-300 text-gray-600",
    secondary: "bg-gray-100 text-gray-800"
  };
  
  const combinedStyles = `${baseStyles} ${variantStyles[variant]} ${className}`;
  
  return (
    <span className={combinedStyles}>
      {children}
    </span>
  );
};

export default SimpleBadge;
