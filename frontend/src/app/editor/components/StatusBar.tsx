// components/StatusBar.tsx
import React from 'react';
import { CursorPosition } from '../types';
import { PencilLine } from 'lucide-react';
import { TypingUser } from './TypingIndicator';

interface StatusBarProps {
  fileName: string;
  language: string;
  isPythonFile: boolean;
  bracketMatching: boolean;
  cursorPosition: CursorPosition;
  isDarkTheme: boolean;
  autoSaveEnabled?: boolean;
  lastSaved?: Date | null;
  modifiedSinceLastSave?: boolean;
  isCollaborative?: boolean;
  lastEditBy?: string | null;
  typingUsers?: TypingUser[];
  currentUserEmail?: string;
}

export function StatusBar({
  fileName,
  language,
  isPythonFile,
  bracketMatching,
  cursorPosition,
  isDarkTheme,
  autoSaveEnabled,
  lastSaved,
  modifiedSinceLastSave,
  isCollaborative,
  lastEditBy,
  typingUsers = [],
  currentUserEmail = ''
}: StatusBarProps) {
  // Format the file type display
  const fileType = fileName.split('.').pop()?.toUpperCase() || 'TXT';
  
  // Format the last saved time
  const formattedLastSaved = lastSaved 
    ? lastSaved.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
    : '';
    
  // Filter out the current user from typing users
  const otherTypingUsers = typingUsers.filter(user => user.email !== currentUserEmail);
  
  return (
    <div className={`text-xs ${isDarkTheme ? 'text-gray-400' : 'text-gray-500'} flex justify-between border-t pt-1`}>
      <div className="flex items-center space-x-2 flex-wrap">
        <span title="Current file">
          {fileName}
        </span>
        <span className="px-1 py-0.5 rounded text-xs bg-blue-500 text-white" title="File type">
          {fileType}
        </span>
        <span title="Language mode">
          {language}
        </span>
        {isPythonFile && (
          <span className="text-green-500" title="Python auto-indent enabled">
            Python indent
          </span>
        )}
        {bracketMatching && (
          <span className="text-blue-500" title="Bracket matching enabled">
            Bracket matching
          </span>
        )}
        {autoSaveEnabled !== undefined && (
          <span className={autoSaveEnabled ? 'text-green-500' : 'text-gray-500'} title="Auto-save status">
            {autoSaveEnabled ? 'Auto-save on' : 'Auto-save off'}
          </span>
        )}
        {lastSaved && (
          <span title="Last saved time" className={modifiedSinceLastSave ? 'text-yellow-500' : 'text-green-500'}>
            {modifiedSinceLastSave ? 'Modified' : 'Saved'}: {formattedLastSaved}
          </span>
        )}
        {isCollaborative && (
          <span className="px-2 py-0.5 rounded bg-purple-500 text-white" title="Collaborative mode active">
            Collaborative
          </span>
        )}
        {isCollaborative && lastEditBy && (
          <span className="text-purple-500" title="Last editor">
            Last edit by: {lastEditBy}
          </span>
        )}
        {isCollaborative && otherTypingUsers.length > 0 && (
          <span 
            className="flex items-center gap-1 text-purple-400"
            title={otherTypingUsers.map(u => u.name || u.email.split('@')[0]).join(', ') + ' typing...'}
          >
            <PencilLine className="h-3 w-3 animate-pulse" />
            {otherTypingUsers.length === 1 ? (
              <span className="truncate max-w-[100px]">
                {otherTypingUsers[0].name || otherTypingUsers[0].email.split('@')[0]}
                <span className="animate-pulse">...</span>
              </span>
            ) : (
              <span>
                {otherTypingUsers.length} typing
                <span className="animate-pulse">...</span>
              </span>
            )}
          </span>
        )}
        {isCollaborative && (
          <style jsx global>{`
            @keyframes fade-in {
              from { opacity: 0; transform: translateY(5px); }
              to { opacity: 1; transform: translateY(0); }
            }
            
            @keyframes pulse {
              0% { opacity: 0.4; }
              50% { opacity: 1; }
              100% { opacity: 0.4; }
            }
            
            .animate-fade-in {
              animation: fade-in 0.3s ease-out;
            }
            
            .animate-pulse {
              animation: pulse 1.5s infinite;
            }
          `}</style>
        )}
      </div>
      <div className="flex items-center space-x-2">
        <span title="Current cursor position">
          Line {cursorPosition.line}, Column {cursorPosition.column}
        </span>
        <span className={`ml-2 px-1 rounded ${isDarkTheme ? 'bg-gray-700' : 'bg-gray-200'}`} title="Encoding">
          UTF-8
        </span>
        <span className={`px-1 rounded ${isDarkTheme ? 'bg-gray-700' : 'bg-gray-200'}`} title="Line endings">
          LF
        </span>
      </div>
    </div>
  );
}
