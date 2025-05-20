import { useState, useCallback } from 'react';

interface EditorUIState {
  fontSize: number;
  showLineNumbers: boolean;
  isHighlighting: boolean;
  showDebugPanel: boolean;
  keyboardShortcutsExpanded: boolean;
  logoSize: number;
  showSettings: boolean;
  // New tab overflow properties
  isTabOverflowing: boolean;
  tabDropdownOpen: boolean;
}

interface EditorUIStateOptions {
  /**
   * Initial font size
   * @default 14
   */
  initialFontSize?: number;
  
  /**
   * Initial logo size
   * @default 24
   */
  initialLogoSize?: number;
}

export function useEditorUIState(options: EditorUIStateOptions = {}) {
  const {
    initialFontSize = 14,
    initialLogoSize = 24
  } = options;

  const [uiState, setUiState] = useState<EditorUIState>({
    fontSize: initialFontSize,
    showLineNumbers: true,
    isHighlighting: true,
    showDebugPanel: false,
    keyboardShortcutsExpanded: false,
    logoSize: initialLogoSize,
    showSettings: false,
    // Initialize new tab overflow properties
    isTabOverflowing: false,
    tabDropdownOpen: false
  });

  // Font size methods
  const setFontSize = useCallback((size: number) => {
    setUiState(prev => ({ ...prev, fontSize: size }));
  }, []);

  // Toggle methods
  const toggleLineNumbers = useCallback(() => {
    setUiState(prev => ({ ...prev, showLineNumbers: !prev.showLineNumbers }));
  }, []);

  const toggleHighlighting = useCallback(() => {
    setUiState(prev => ({ ...prev, isHighlighting: !prev.isHighlighting }));
  }, []);

  const toggleDebugPanel = useCallback(() => {
    setUiState(prev => ({ ...prev, showDebugPanel: !prev.showDebugPanel }));
  }, []);

  const toggleKeyboardShortcuts = useCallback(() => {
    setUiState(prev => ({ 
      ...prev, 
      keyboardShortcutsExpanded: !prev.keyboardShortcutsExpanded 
    }));
  }, []);

  // Logo size methods
  const increaseLogo = useCallback(() => {
    setUiState(prev => ({ 
      ...prev, 
      logoSize: Math.min(prev.logoSize + 1, 40) 
    }));
  }, []);

  const decreaseLogo = useCallback(() => {
    setUiState(prev => ({ 
      ...prev, 
      logoSize: Math.max(prev.logoSize - 1, 16) 
    }));
  }, []);

  // Settings panel methods
  const toggleSettings = useCallback(() => {
    setUiState(prev => ({ ...prev, showSettings: !prev.showSettings }));
  }, []);

  // Tab overflow methods
  const setTabOverflow = useCallback((isOverflowing: boolean) => {
    setUiState(prev => ({
      ...prev,
      isTabOverflowing: isOverflowing
    }));
  }, []);

  const toggleTabDropdown = useCallback(() => {
    setUiState(prev => ({
      ...prev,
      tabDropdownOpen: !prev.tabDropdownOpen
    }));
  }, []);

  const closeTabDropdown = useCallback(() => {
    setUiState(prev => ({
      ...prev,
      tabDropdownOpen: false
    }));
  }, []);

  return {
    /**
     * Current UI state
     */
    uiState,

    /**
     * Methods to manipulate UI state
     */
    methods: {
      setFontSize,
      toggleLineNumbers,
      toggleHighlighting,
      toggleDebugPanel,
      toggleKeyboardShortcuts,
      increaseLogo,
      decreaseLogo,
      toggleSettings,
      // New tab overflow methods
      setTabOverflow,
      toggleTabDropdown,
      closeTabDropdown
    }
  };
}
