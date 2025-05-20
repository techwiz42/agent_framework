// components/KeyboardShortcutsHelp.tsx
import React from 'react';

interface KeyboardShortcutsHelpProps {
  isDarkTheme: boolean;
  expanded?: boolean;
  toggleExpanded?: () => void;
}

interface ShortcutInfo {
  key: string;
  description: string;
  modifier?: string;
}

export function KeyboardShortcutsHelp({ 
  isDarkTheme, 
  expanded = false, 
  toggleExpanded 
}: KeyboardShortcutsHelpProps) {
  // Define all shortcuts
  const shortcuts: ShortcutInfo[] = [
    { key: 'S', description: 'Save', modifier: 'Ctrl' },
    { key: 'F', description: 'Find/Replace', modifier: 'Ctrl' },
    { key: 'G', description: 'Go to Line', modifier: 'Ctrl' },
    { key: '[', description: 'Decrease Indent', modifier: 'Ctrl' },
    { key: ']', description: 'Increase Indent', modifier: 'Ctrl' },
    { key: 'D', description: 'Duplicate Line', modifier: 'Ctrl' },
    { key: '/', description: 'Toggle Comment', modifier: 'Ctrl' },
    { key: 'Tab', description: 'Indent Selection' },
    { key: 'Tab', description: 'Unindent Selection', modifier: 'Shift' },
    { key: 'Enter', description: 'Smart Indent' }
  ];
  
  // Show just the basic shortcuts in compact mode
  const displayedShortcuts = expanded 
    ? shortcuts 
    : shortcuts.slice(0, 6);
  
  return (
    <div className={`mt-1 text-xs ${isDarkTheme ? 'text-gray-400' : 'text-gray-600'}`}>
      <div className="flex flex-wrap items-center">
        {displayedShortcuts.map((shortcut, index) => (
          <span key={index} className="mr-4 whitespace-nowrap">
            <kbd className={`px-1 py-0.5 rounded ${
              isDarkTheme ? 'bg-gray-700 text-gray-300' : 'bg-gray-200'
            }`}>
              {shortcut.modifier && (
                <>{shortcut.modifier}+</>
              )}
              {shortcut.key}
            </kbd>
            {' '}
            {shortcut.description}
          </span>
        ))}
        
        {toggleExpanded && (
          <button 
            onClick={toggleExpanded}
            className={`text-xs underline ${
              isDarkTheme ? 'text-blue-400' : 'text-blue-600'
            }`}
          >
            {expanded ? 'Show Less' : 'More Shortcuts...'}
          </button>
        )}
      </div>
    </div>
  );
}
