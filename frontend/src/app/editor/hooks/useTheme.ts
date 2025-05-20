// hooks/useTheme.ts
import { useState, useEffect } from 'react';
import { ThemeState } from '../types';

export function useTheme() {
  const [theme, setTheme] = useState<ThemeState>({
    isDark: false,
    currentTheme: 'prism',
    availableThemes: ['prism', 'okaidia', 'solarizedlight', 'tomorrow', 'dark']
  });
  
  // Load theme CSS
  useEffect(() => {
    // Remove any existing theme stylesheets
    const existingLink = document.getElementById('prism-theme-stylesheet');
    if (existingLink) {
      existingLink.remove();
    }
    
    // Add the new theme stylesheet
    const link = document.createElement('link');
    link.id = 'prism-theme-stylesheet';
    link.rel = 'stylesheet';
    
    // Select the appropriate theme CSS
    if (theme.isDark) {
      if (theme.currentTheme === 'dark') {
        link.href = 'https://cdnjs.cloudflare.com/ajax/libs/prism/1.24.1/themes/prism-dark.min.css';
      } else if (theme.currentTheme === 'okaidia') {
        link.href = 'https://cdnjs.cloudflare.com/ajax/libs/prism/1.24.1/themes/prism-okaidia.min.css';
      } else if (theme.currentTheme === 'tomorrow') {
        link.href = 'https://cdnjs.cloudflare.com/ajax/libs/prism/1.24.1/themes/prism-tomorrow.min.css';
      } else {
        // Default dark theme
        link.href = 'https://cdnjs.cloudflare.com/ajax/libs/prism/1.24.1/themes/prism-okaidia.min.css';
      }
    } else {
      if (theme.currentTheme === 'solarizedlight') {
        link.href = 'https://cdnjs.cloudflare.com/ajax/libs/prism/1.24.1/themes/prism-solarizedlight.min.css';
      } else {
        // Default light theme
        link.href = 'https://cdnjs.cloudflare.com/ajax/libs/prism/1.24.1/themes/prism.min.css';
      }
    }
    
    document.head.appendChild(link);
    
    // Update editor background based on theme
    if (theme.isDark) {
      document.documentElement.classList.add('dark-theme');
    } else {
      document.documentElement.classList.remove('dark-theme');
    }
  }, [theme]);
  
  // Load theme from localStorage on initial render
  useEffect(() => {
    try {
      const savedTheme = localStorage.getItem('editor-theme');
      if (savedTheme) {
        setTheme(JSON.parse(savedTheme));
      }
    } catch (error) {
      console.error('Failed to load theme from localStorage:', error);
    }
  }, []);
  
  // Save theme to localStorage whenever it changes
  useEffect(() => {
    try {
      localStorage.setItem('editor-theme', JSON.stringify(theme));
    } catch (error) {
      console.error('Failed to save theme to localStorage:', error);
    }
  }, [theme]);
  
  const toggleTheme = () => {
    setTheme(prev => ({
      ...prev,
      isDark: !prev.isDark
    }));
  };
  
  const changeTheme = (themeName: string) => {
    setTheme(prev => ({
      ...prev,
      currentTheme: themeName
    }));
  };
  
  return {
    theme,
    toggleTheme,
    changeTheme
  };
}
