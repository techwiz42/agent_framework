// components/SettingsPanel.tsx
import React from 'react';

interface SettingsPanelProps {
  isVisible: boolean;
  onClose: () => void;
  isDarkTheme: boolean;
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
  currentTheme: string;
  availableThemes: string[];
  changeTheme: (themeName: string) => void;
  toggleTheme: () => void;
}

export function SettingsPanel({
  isVisible,
  onClose,
  isDarkTheme,
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
  currentTheme,
  availableThemes,
  changeTheme,
  toggleTheme
}: SettingsPanelProps) {
  if (!isVisible) return null;

  // Friendly display names for themes
  const themeDisplayNames: Record<string, string> = {
    'prism': 'Default Light',
    'okaidia': 'Okaidia Dark',
    'solarizedlight': 'Solarized Light',
    'tomorrow': 'Tomorrow Night',
    'dark': 'Dark Theme'
  };

  // Explicitly define theme modes
  const themeMode: Record<string, 'light' | 'dark'> = {
    'prism': 'light',
    'solarizedlight': 'light',
    'okaidia': 'dark',
    'tomorrow': 'dark',
    'dark': 'dark'
  };

  // Filter themes based on current mode
  const filteredThemes = availableThemes.filter(themeName => {
    const themeIsLight = themeMode[themeName] === 'light';
    const result = isDarkTheme ? !themeIsLight : themeIsLight;
    return result;
  });

  return (
    <div 
      className={`absolute right-0 top-14 z-50 p-4 rounded shadow-lg ${
        isDarkTheme ? 'bg-gray-700 text-white' : 'bg-white text-black'
      }`}
      style={{ width: '300px', maxHeight: '80vh', overflowY: 'auto' }}
    >
      <h3 className="font-medium mb-4 text-lg border-b pb-2">Editor Settings</h3>
      
      {/* Theme Settings */}
      <div className="mb-4">
        <h4 className="text-sm font-medium border-b pb-1 mb-2">Theme</h4>
        <div className="flex items-center space-x-2 mb-2">
          <label className="text-sm mr-2">Mode:</label>
          <button
            onClick={toggleTheme}
            className={`px-2 py-1 rounded ${
              isDarkTheme 
                ? 'bg-blue-600 text-white' 
                : 'bg-gray-200 text-black'
            }`}
          >
            {isDarkTheme ? 'Dark' : 'Light'}
          </button>
        </div>
        <div className="flex flex-wrap gap-2">
          {filteredThemes.map(themeName => (
            <button
              key={themeName}
              className={`px-2 py-1 rounded text-xs ${
                currentTheme === themeName 
                  ? 'bg-blue-600 text-white' 
                  : isDarkTheme 
                    ? 'bg-gray-600 text-gray-200' 
                    : 'bg-gray-200 text-black'
              }`}
              onClick={() => changeTheme(themeName)}
              title={`Switch to ${themeDisplayNames[themeName]} theme`}
            >
              {themeDisplayNames[themeName] || themeName.charAt(0).toUpperCase() + themeName.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Font Size Setting */}
      <div className="mb-4">
        <label className="block text-sm mb-2">Font Size</label>
        <div className="flex items-center">
          <select
            value={fontSize}
            onChange={(e) => setFontSize(Number(e.target.value))}
            className={`w-full p-2 rounded ${
              isDarkTheme 
                ? 'bg-gray-600 text-white border-gray-500' 
                : 'bg-gray-100 text-black border-gray-300'
            }`}
          >
            {[10, 12, 14, 16, 18, 20, 22, 24].map(size => (
              <option key={size} value={size}>{size}px</option>
            ))}
          </select>
        </div>
      </div>

      {/* Editor Features */}
      <div className="space-y-3">
        <h4 className="text-sm font-medium border-b pb-1">Editor Features</h4>
        
        <div className="flex items-center justify-between">
          <label htmlFor="line-numbers" className="text-sm">Show Line Numbers</label>
          <input
            type="checkbox"
            id="line-numbers"
            checked={showLineNumbers}
            onChange={() => setShowLineNumbers(!showLineNumbers)}
          />
        </div>

        <div className="flex items-center justify-between">
          <label htmlFor="syntax-highlight" className="text-sm">Syntax Highlighting</label>
          <input
            type="checkbox"
            id="syntax-highlight"
            checked={isHighlighting}
            onChange={() => setIsHighlighting(!isHighlighting)}
          />
        </div>

        <div className="flex items-center justify-between">
          <label htmlFor="code-folding" className="text-sm">Code Folding</label>
          <input
            type="checkbox"
            id="code-folding"
            checked={folding.enabled}
            onChange={toggleFolding}
          />
        </div>

        <div className="flex items-center justify-between">
          <label htmlFor="bracket-matching" className="text-sm">Bracket Matching</label>
          <input
            type="checkbox"
            id="bracket-matching"
            checked={bracketMatching}
            onChange={toggleBracketMatching}
          />
        </div>
      </div>

      <button 
        onClick={onClose}
        className={`mt-4 w-full py-2 rounded ${
          isDarkTheme 
            ? 'bg-blue-600 hover:bg-blue-700' 
            : 'bg-blue-500 hover:bg-blue-600'
        } text-white`}
      >
        Close Settings
      </button>
    </div>
  );
}
