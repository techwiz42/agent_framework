// components/Toolbar.tsx
import React from 'react';
import { Save, Search, Copy, Check, Moon, Sun } from 'lucide-react';
import { DownloadButton } from '@/app/conversations/[id]/components/DownloadButton';
import { AutoSaveState } from '../types';

interface ToolbarProps {
  currentTabContent: string;
  currentFileName: string;
  currentFileType: string;
  fontSize: number;
  setFontSize: (size: number) => void;
  showLineNumbers: boolean;
  setShowLineNumbers: (show: boolean) => void;
  isHighlighting: boolean;
  setIsHighlighting: (highlight: boolean) => void;
  folding: { enabled: boolean };
  toggleFolding: () => void;
  bracketMatching: boolean;
  toggleBracketMatching: () => void;
  autoSave: AutoSaveState;
  toggleAutoSave: () => void;
  handleSave: () => void;
  handleCopy: () => void;
  copyStatus: 'idle' | 'copied' | 'failed';
  openFindReplace: () => void;
  toggleTheme: () => void;
  isDarkTheme: boolean;
  closeEditor: () => void;
}

export function Toolbar({
  currentTabContent,
  currentFileName,
  currentFileType,
  fontSize,
  setFontSize,
  showLineNumbers,
  setShowLineNumbers,
  isHighlighting,
  setIsHighlighting,
  folding,
  toggleFolding,
  bracketMatching,
  toggleBracketMatching,
  autoSave,
  toggleAutoSave,
  handleSave,
  handleCopy,
  copyStatus,
  openFindReplace,
  toggleTheme,
  isDarkTheme,
  closeEditor
}: ToolbarProps) {
  return (
    <div className="flex flex-col space-y-2">
      {/* Main toolbar */}
      <div className="flex items-center justify-between border-t pt-2">
        <div className="flex space-x-2">
          <DownloadButton
            content={currentTabContent}
            defaultFileName={currentFileName.split('.')[0] || 'download'}
            currentFileType={currentFileType || 'txt'}
          />
          <button
            onClick={handleCopy}
            className={`px-3 py-1 ${
              copyStatus === 'copied' 
                ? 'bg-green-500' 
                : copyStatus === 'failed' 
                  ? 'bg-red-500' 
                  : 'bg-gray-500'
            } text-white rounded hover:opacity-90 flex items-center`}
            title="Copy to clipboard"
          >
            {copyStatus === 'copied' 
              ? <><Check className="h-4 w-4 mr-1" /> Copied!</> 
              : <><Copy className="h-4 w-4 mr-1" /> Copy</>
            }
          </button>
          <button
            onClick={handleSave}
            className="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 flex items-center"
            title="Save (Ctrl+S)"
          >
            <Save className="h-4 w-4 mr-1" /> Save
          </button>
          <button
            onClick={openFindReplace}
            className="px-3 py-1 bg-purple-500 text-white rounded hover:bg-purple-600 flex items-center"
            title="Find/Replace (Ctrl+F)"
          >
            <Search className="h-4 w-4 mr-1" /> Find
          </button>
        </div>

        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={autoSave.enabled}
              onChange={toggleAutoSave}
              id="auto-save"
            />
            <label htmlFor="auto-save" className="text-sm flex items-center">
              Auto-Save
              {autoSave.lastSaved && (
                <span className="text-xs text-gray-500 ml-1">
                  ({autoSave.lastSaved.toLocaleTimeString()})
                </span>
              )}
            </label>
          </div>

          <div className="flex items-center space-x-2">
            <label className="text-sm">Font:</label>
            <select
              value={fontSize}
              onChange={(e) => setFontSize(Number(e.target.value))}
              className={`border rounded p-1 ${isDarkTheme ? 'bg-gray-700 text-white border-gray-600' : ''}`}
            >
              {[10, 12, 14, 16, 18, 20, 22, 24].map(size => (
                <option key={size} value={size}>{size}px</option>
              ))}
            </select>
          </div>

          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={showLineNumbers}
              onChange={() => setShowLineNumbers(!showLineNumbers)}
              id="line-numbers"
            />
            <label htmlFor="line-numbers" className="text-sm">Line Numbers</label>
          </div>

          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={isHighlighting}
              onChange={() => setIsHighlighting(!isHighlighting)}
              id="syntax-highlight"
            />
            <label htmlFor="syntax-highlight" className="text-sm">Highlighting</label>
          </div>

          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={folding.enabled}
              onChange={toggleFolding}
              id="code-folding"
            />
            <label htmlFor="code-folding" className="text-sm">Code Folding</label>
          </div>

          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={bracketMatching}
              onChange={toggleBracketMatching}
              id="bracket-matching"
            />
            <label htmlFor="bracket-matching" className="text-sm">Bracket Matching</label>
          </div>

          <button
            onClick={toggleTheme}
            className="p-1 rounded-full"
            title={isDarkTheme ? "Switch to Light Mode" : "Switch to Dark Mode"}
          >
            {isDarkTheme ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
          </button>

          <button
            onClick={closeEditor}
            className="px-3 py-1 bg-red-500 text-white rounded hover:bg-red-600"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
