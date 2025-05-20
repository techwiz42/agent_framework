// components/TypingIndicator.tsx
import React from 'react';
import { PencilLine } from 'lucide-react';

export interface TypingUser {
  email: string;
  name?: string;
  timestamp: Date;
}

interface TypingIndicatorProps {
  typingUsers: TypingUser[];
  currentUserEmail: string;
  isDarkTheme: boolean;
}

export function TypingIndicator({
  typingUsers,
  currentUserEmail,
  isDarkTheme
}: TypingIndicatorProps) {
  // Don't show anything if no one is typing or only the current user is typing
  if (typingUsers.length === 0 || (typingUsers.length === 1 && typingUsers[0].email === currentUserEmail)) {
    return null;
  }
  
  // Filter out the current user
  const otherTypingUsers = typingUsers.filter(user => user.email !== currentUserEmail);
  
  if (otherTypingUsers.length === 0) {
    return null;
  }
  
  return (
    <div 
      className={`
        absolute bottom-0 left-0 z-10 px-2 py-1
        flex items-center space-x-1 border-t border-r
        text-xs opacity-80 hover:opacity-100 transition-opacity duration-200
        ${isDarkTheme ? 'bg-gray-800 text-gray-300 border-gray-700' : 'bg-gray-100 text-gray-700 border-gray-200'}
      `}
      style={{ borderTopRightRadius: '4px' }}
    >
      <PencilLine className="h-3 w-3 animate-pulse" />
      
      <div className="flex items-center gap-1 max-w-[150px] overflow-hidden">
        {otherTypingUsers.length === 1 ? (
          <span className="truncate">
            {otherTypingUsers[0].name || otherTypingUsers[0].email.split('@')[0]}
          </span>
        ) : (
          <span className="truncate">
            {otherTypingUsers.length} collaborators
          </span>
        )}
      </div>
      
      <span className="animate-pulse leading-tight">...</span>
    </div>
  );
}
