// components/ThemeSelector.tsx
import React from 'react';
import { ThemeState } from '../types';

interface ThemeSelectorProps {
  theme: ThemeState;
  changeTheme: (themeName: string) => void;
}

export function ThemeSelector({ theme, changeTheme }: ThemeSelectorProps) {
  // Filter themes based on current mode (dark/light)
  const availableThemes = theme.isDark 
    ? theme.availableThemes.filter(t => t !== 'prism' && t !== 'solarizedlight')
    : theme.availableThemes.filter(t => t === 'prism' || t === 'solarizedlight');

  // Friendly display names for themes
  const themeDisplayNames: Record<string, string> = {
    'prism': 'Default',
    'okaidia': 'Okaidia',
    'solarizedlight': 'Solarized',
    'tomorrow': 'Tomorrow',
    'dark': 'Dark'
  };
  
  return (
    <div className={`flex items-center space-x-2 text-sm mt-1 pt-1 ${
      theme.isDark ? 'border-t border-gray-600' : 'border-t border-gray-200'
    }`}>
      <span>Theme:</span>
      {availableThemes.map(themeName => (
        <button
          key={themeName}
          className={`px-2 py-1 rounded ${
            theme.currentTheme === themeName 
              ? 'bg-blue-600 text-white' 
              : theme.isDark 
                ? 'bg-gray-600' 
                : 'bg-gray-200'
          }`}
          onClick={() => changeTheme(themeName)}
          title={`Switch to ${themeDisplayNames[themeName]} theme`}
        >
          {themeDisplayNames[themeName] || themeName.charAt(0).toUpperCase() + themeName.slice(1)}
        </button>
      ))}
    </div>
  );
}
