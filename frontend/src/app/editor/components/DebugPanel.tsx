// components/DebugPanel.tsx
import React from 'react';
import { CursorPosition, AutoSaveState, ThemeState, FoldingState, EditorTab } from '../types';

// Define a type for messages instead of using 'any'
export interface EditorMessage {
  id: string;
  type: 'info' | 'warning' | 'error' | 'success';
  content: string;
  timestamp: Date;
}

interface DebugPanelProps {
  editorState: {
    tabs: EditorTab[];
    activeTab: number;
    messages: EditorMessage[]; // Use the new type here instead of any[]
  };
  cursorPosition: CursorPosition;
  autoSave: AutoSaveState;
  theme: ThemeState;
  folding: FoldingState;
  bracketMatching: boolean;
  sessionId?: string | null;
}

export function DebugPanel({
  editorState,
  cursorPosition,
  autoSave,
  theme,
  folding,
  bracketMatching,
  sessionId
}: DebugPanelProps) {
  const activeTab = editorState.tabs[editorState.activeTab];
  
  // Format values for display
  const formatDate = (date: Date | null) => {
    if (!date) return 'Never';
    return date.toLocaleString();
  };
  
  // Calculate current content stats
  const calculateContentStats = () => {
    if (!activeTab) return { lines: 0, chars: 0, words: 0 };
    
    const content = activeTab.content;
    const lines = content.split('\n').length;
    const chars = content.length;
    const words = content.split(/\s+/).filter(Boolean).length;
    
    return { lines, chars, words };
  };
  
  const stats = calculateContentStats();
  
  return (
    <div className="mt-2 p-4 bg-gray-800 text-white rounded overflow-auto" style={{ maxHeight: '300px' }}>
      <h3 className="font-bold mb-2">Debug Information</h3>
      
      <div className="grid grid-cols-2 gap-4">
        <div>
          <h4 className="font-semibold text-blue-300 mb-1">Editor State</h4>
          <p>Session ID: {sessionId || 'None'}</p>
          <p>Current file: {activeTab?.fileName || 'None'}</p>
          <p>File type: {activeTab?.fileType || 'None'}</p>
          <p>Open tabs: {editorState.tabs.length}</p>
          <p>Cursor position: Line {cursorPosition.line}, Column {cursorPosition.column}</p>
          
          <h4 className="font-semibold text-blue-300 mt-3 mb-1">Content Stats</h4>
          <p>Lines: {stats.lines}</p>
          <p>Characters: {stats.chars}</p>
          <p>Words: {stats.words}</p>
        </div>
        
        <div>
          <h4 className="font-semibold text-blue-300 mb-1">Features</h4>
          <p>Auto-save: {autoSave.enabled ? 'Enabled' : 'Disabled'}</p>
          <p>Auto-save interval: {autoSave.interval / 1000}s</p>
          <p>Last saved: {formatDate(autoSave.lastSaved)}</p>
          <p>Theme: {theme.isDark ? 'Dark' : 'Light'} ({theme.currentTheme})</p>
          <p>Folding: {folding.enabled ? 'Enabled' : 'Disabled'}</p>
          <p>Folded regions: {folding.foldedLines.size}</p>
          <p>Bracket matching: {bracketMatching ? 'Enabled' : 'Disabled'}</p>
        </div>
      </div>
      
      <h4 className="font-semibold text-blue-300 mt-3 mb-1">Message Log ({editorState.messages.length})</h4>
      <div className="bg-gray-900 p-2 rounded max-h-32 overflow-auto">
        {editorState.messages.length === 0 ? (
          <p className="text-gray-500 italic">No messages received</p>
        ) : (
          <pre className="text-xs text-gray-300 whitespace-pre-wrap">
            {JSON.stringify(editorState.messages.slice(-5), null, 2)}
            {editorState.messages.length > 5 && (
              <p className="text-gray-500 mt-1">
                ... and {editorState.messages.length - 5} more messages
              </p>
            )}
          </pre>
        )}
      </div>
    </div>
  );
}
