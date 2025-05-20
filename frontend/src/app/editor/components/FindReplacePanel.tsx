// components/FindReplacePanel.tsx
import React from 'react';
import { FindReplaceState } from '../types';

interface FindReplacePanelProps {
  findReplace: FindReplaceState;
  setFindReplace: React.Dispatch<React.SetStateAction<FindReplaceState>>;
  findText: (direction: 'next' | 'prev') => void;
  replaceText: (replaceAll?: boolean) => void;
  isDarkTheme: boolean;
}

export function FindReplacePanel({
  findReplace,
  setFindReplace,
  findText,
  replaceText,
  isDarkTheme
}: FindReplacePanelProps) {
  // Handle input changes
  const handleFindTextChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFindReplace(prev => ({ 
      ...prev, 
      findText: e.target.value,
      currentMatch: 0,
      matches: 0
    }));
  };

  const handleReplaceTextChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFindReplace(prev => ({ ...prev, replaceText: e.target.value }));
  };

  const handleMatchCaseChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFindReplace(prev => ({ ...prev, matchCase: e.target.checked }));
  };

  const handleWholeWordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFindReplace(prev => ({ ...prev, wholeWord: e.target.checked }));
  };

  const closePanel = () => {
    setFindReplace(prev => ({ ...prev, visible: false }));
  };
  
  return (
    <div className={`p-2 border-t ${isDarkTheme ? 'border-gray-600' : 'border-gray-200'}`}>
      <div className="flex flex-wrap items-center gap-2">
        <div className="flex items-center">
          <input
            type="text"
            placeholder="Find"
            value={findReplace.findText}
            onChange={handleFindTextChange}
            className={`border rounded p-1 w-40 ${isDarkTheme ? 'bg-gray-700 text-white border-gray-600' : ''}`}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                findText('next');
              }
            }}
          />
          <div className="text-xs ml-2">
            {findReplace.matches > 0 && `${findReplace.currentMatch}/${findReplace.matches}`}
          </div>
        </div>

        <input
          type="text"
          placeholder="Replace"
          value={findReplace.replaceText}
          onChange={handleReplaceTextChange}
          className={`border rounded p-1 w-40 ${isDarkTheme ? 'bg-gray-700 text-white border-gray-600' : ''}`}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && e.shiftKey) {
              replaceText(true); // Replace all
            } else if (e.key === 'Enter') {
              replaceText(); // Replace current
            }
          }}
        />

        <button
          onClick={() => findText('prev')}
          className={`px-2 py-1 rounded ${
            isDarkTheme ? 'bg-gray-600 text-white' : 'bg-gray-200'
          } ${findReplace.findText ? '' : 'opacity-50 cursor-not-allowed'}`}
          disabled={!findReplace.findText}
          title="Previous match (Shift+Enter)"
        >
          ↑
        </button>

        <button
          onClick={() => findText('next')}
          className={`px-2 py-1 rounded ${
            isDarkTheme ? 'bg-gray-600 text-white' : 'bg-gray-200'
          } ${findReplace.findText ? '' : 'opacity-50 cursor-not-allowed'}`}
          disabled={!findReplace.findText}
          title="Next match (Enter)"
        >
          ↓
        </button>

        <button
          onClick={() => replaceText()}
          className={`px-2 py-1 bg-blue-500 text-white rounded ${
            findReplace.findText ? '' : 'opacity-50 cursor-not-allowed'
          }`}
          disabled={!findReplace.findText}
          title="Replace current (Enter in Replace field)"
        >
          Replace
        </button>

        <button
          onClick={() => replaceText(true)}
          className={`px-2 py-1 bg-blue-600 text-white rounded ${
            findReplace.findText ? '' : 'opacity-50 cursor-not-allowed'
          }`}
          disabled={!findReplace.findText}
          title="Replace all (Shift+Enter in Replace field)"
        >
          Replace All
        </button>

        <div className="flex items-center space-x-2 ml-4">
          <input
            type="checkbox"
            id="match-case"
            checked={findReplace.matchCase}
            onChange={handleMatchCaseChange}
          />
          <label htmlFor="match-case" className="text-sm">Match case</label>

          <input
            type="checkbox"
            id="whole-word"
            checked={findReplace.wholeWord}
            onChange={handleWholeWordChange}
            className="ml-2"
          />
          <label htmlFor="whole-word" className="text-sm">Whole word</label>
        </div>

        <button
          onClick={closePanel}
          className={`ml-auto px-2 py-1 rounded ${isDarkTheme ? 'bg-gray-600' : 'bg-gray-200'}`}
          title="Close panel (Escape)"
        >
          Close
        </button>
      </div>
    </div>
  );
}
