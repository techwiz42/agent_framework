'use client';

import React, { useRef, useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';

// Import Lucide icons
import { Settings } from 'lucide-react';

// Import components
import { TabBar } from './components/TabBar';
import { FindReplacePanel } from './components/FindReplacePanel';
import { StatusBar } from './components/StatusBar';
import { EditorArea } from './components/EditorArea';
import { ThemeSelector } from './components/ThemeSelector';
import { KeyboardShortcutsHelp } from './components/KeyboardShortcutsHelp';
import { DebugPanel } from './components/DebugPanel';
import { DownloadButton } from '@/app/conversations/[id]/components/DownloadButton';
import { SettingsPanel } from './components/SettingsPanel';

// Import hooks
import { useEditorState } from './hooks/useEditorState';
import { useTheme } from './hooks/useTheme';
import { useFolding } from './hooks/useFolding';
import { useBracketMatching } from './hooks/useBracketMatching';
import { useAutoSave } from './hooks/useAutoSave';
import { useKeyboardShortcuts } from './hooks/useKeyboardShortcuts';
import { useCopyPaste } from './hooks/useCopyPaste';
import { useCursorPosition } from './hooks/useCursorPosition';
import { useSyntaxHighlighting } from './hooks/useSyntaxHighlighting';
import { useEditorUIState } from './hooks/useEditorUIState';
import { useEditorFeatures } from './hooks/useEditorFeatures';
import { useCollaborativeEditor } from './hooks/useCollaborativeEditor';
import { useTypingIndicator } from './hooks/useTypingIndicator';
import { participantStorage } from '@/lib/participantStorage';
import { websocketService } from '@/services/websocket';

// Import types
import { FindReplaceState } from './types';
import { WebSocketMessage } from '@/types/websocket.types';

export default function SimpleEditorPage() {
  const searchParams = useSearchParams();
  const sessionId = searchParams.get('session');
  const conversationId = searchParams.get('conversationId');
  
  // Refs
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  
  // Core editor state management
  const editor = useEditorState(sessionId);
  const currentTab = editor.tabs[editor.activeTab];

  // Get current user email from participantStorage
  const currentUserEmail = conversationId 
    ? participantStorage.getSession(conversationId)?.email || ''
    : '';
    
  // Collaborative editing
  const collaboration = useCollaborativeEditor(
    sessionId,
    editor.tabs,
    editor.activeTab,
    conversationId || undefined
  );
  
  // Typing indicator
  const typingIndicator = useTypingIndicator({
    conversationId: conversationId || undefined,
    currentUserEmail: currentUserEmail,
    isCollaborationEnabled: collaboration.isCollaborationEnabled
  });
  
  // UI State Management
  const { uiState, methods: uiMethods } = useEditorUIState();
  
  // Theme management
  const { theme, toggleTheme, changeTheme } = useTheme();
  
  // Bracket Matching
  const bracketMatching = useBracketMatching(
    editor.tabs, 
    editor.activeTab,
    textareaRef
  );
  
  // Cursor Position
  const { cursorPosition, updateCursorPosition } = useCursorPosition(textareaRef, {
    onBracketMatching: bracketMatching.updateBracketMatching
  });
  
  // Syntax Highlighting
  const { highlightedContent, currentLanguage } = useSyntaxHighlighting({
    content: currentTab?.content || '',
    fileName: currentTab?.fileName || 'untitled.txt',
    isHighlighting: uiState.isHighlighting
  });
  
  // Copy Paste functionality
  const { copyStatus, copyToClipboard } = useCopyPaste();
  
  // Auto-save management
  const autoSave = useAutoSave(sessionId, editor.tabs);
 
  useEffect(() => {
    // Create a handler that processes incoming editor messages
    const handleEditorMessage = (message: WebSocketMessage) => {
      if (!message || !message.type) return;
    
      console.log('Editor message received in page.tsx:', message.type);
      
      // Process different types of messages
      if (message.type === 'editor_change' || message.type === 'editor_open') {
        const update = collaboration.handleIncomingChange(message);
        
        console.log('Update from handleIncomingChange:', update);
        
        if (update && update.tabIndex !== undefined && update.newContent) {
          console.log('Applying update to tab:', update.tabIndex);
          
          // Update the tab content
          editor.setTabs(prevTabs => {
            const newTabs = [...prevTabs];
            if (newTabs[update.tabIndex]) {
              console.log('Before update:', newTabs[update.tabIndex].content.length);
              // Update the content
              newTabs[update.tabIndex].content = update.newContent;
              console.log('After update:', newTabs[update.tabIndex].content.length);
              // Track who made the edit
              newTabs[update.tabIndex].lastEditBy = update.sender?.name || update.sender?.email || 'Unknown';
            }
            return newTabs;
          });
          
          // You might also need to manually refresh the editor view
          if (textareaRef.current && update.tabIndex === editor.activeTab) {
            // Force the textarea to update
            textareaRef.current.value = update.newContent;
          }
          
          // Force a save to persist the changes
          autoSave.forceSave();
        }
      }
    };
    
    // Subscribe to WebSocket for editor events
    if (collaboration.isCollaborationEnabled) {
      console.log('Setting up WebSocket subscription in page.tsx');
      // Only subscribe when collaboration is enabled
      const unsubscribe = websocketService.subscribe(handleEditorMessage);
      return () => unsubscribe();
    }
  }, [
    collaboration.isCollaborationEnabled, 
    collaboration.handleIncomingChange, 
    editor.setTabs,
    editor.activeTab,
    autoSave,
    collaboration,
    editor
    // websocketService is intentionally omitted as it's a singleton service
  ]); 
  // Folding
  const folding = useFolding(editor.tabs, editor.activeTab);
  
  // Editor Features (find/replace, indentation, etc.)
  const editorFeatures = useEditorFeatures({
    currentTab,
    textareaRef,
    handleTabContentChange: editor.handleTabContentChange,
    updateCursorPosition,
    isPythonFile: () => currentTab?.fileName.endsWith('.py') || false
  });
  
  // Find/Replace State
  const [findReplace, setFindReplace] = useState<FindReplaceState>({
    visible: false,
    findText: '',
    replaceText: '',
    matchCase: false,
    wholeWord: false,
    matches: 0,
    currentMatch: 0
  });
  
  // Keyboard Shortcuts
  const keyboardShortcuts = useKeyboardShortcuts(
    editor.tabs,
    editor.activeTab,
    editor.setTabs,
    textareaRef,
    {
      save: autoSave.forceSave,
      find: () => setFindReplace(prev => ({ ...prev, visible: true })),
      goToLine: () => {
        const lineNumberStr = prompt('Go to line:');
        if (!lineNumberStr || isNaN(parseInt(lineNumberStr))) return;
        const lineNumber = parseInt(lineNumberStr);
        
        // Implement go to line logic
        if (lineNumber < 1 || !currentTab) return;
        
        const lines = currentTab.content.split('\n');
        if (lineNumber > lines.length) return;
        
        // Calculate position
        let position = 0;
        for (let i = 0; i < lineNumber - 1; i++) {
          position += lines[i].length + 1; // +1 for newline
        }
        
        // Set cursor position
        if (textareaRef.current) {
          textareaRef.current.focus();
          textareaRef.current.setSelectionRange(position, position);
          updateCursorPosition();
        }
      },
      duplicateLine: editorFeatures.duplicateLine,
      indentSelection: editorFeatures.indentSelection
    }
  );
  
  // Error and Empty State Handling
  if (editor.error) {
    return (
      <div className="p-4">
        <h1 className="text-xl font-bold mb-4 text-red-500">Editor Error</h1>
        <p className="mb-4">{editor.error}</p>
        <button 
          onClick={() => window.close()}
          className="px-4 py-2 bg-blue-500 text-white rounded mr-2"
        >
          Close
        </button>
      </div>
    );
  }

  if (editor.tabs.length === 0) {
    return (
      <div className="p-4">
        <h1 className="text-xl font-bold mb-4">No Files to Edit</h1>
        <p className="mb-4">No files were found to edit. Please try again.</p>
        <button 
          onClick={() => window.close()}
          className="px-4 py-2 bg-blue-500 text-white rounded mr-2"
        >
          Close
        </button>
      </div>
    );
  }

  // Main Editor Render
  return (
    <div className={`p-4 h-screen flex flex-col ${theme.isDark ? 'bg-gray-800 text-white' : 'bg-gray-100'}`}>
      <div className={`${theme.isDark ? 'bg-gray-700' : 'bg-white'} rounded-t shadow-md p-2 flex flex-col space-y-2 relative`}>
        {/* Tab Bar */}
       <TabBar 
         tabs={editor.tabs}
         activeTab={editor.activeTab}
         setActiveTab={editor.setActiveTab}
         handleCloseTab={editor.handleCloseTab}
         handleAddTab={editor.handleAddTab}
         handleRenameTab={editor.handleRenameTab}
         isDarkTheme={theme.isDark}
         logoSize={35}
       /> 
        {/* Toolbar */}
        <div className="flex items-center justify-between border-t pt-2">
          <div className="flex space-x-2">
            <DownloadButton
              content={currentTab?.content || ''}
              defaultFileName={currentTab?.fileName.split('.')[0] || 'download'}
              currentFileType={currentTab?.fileType || 'txt'}
            />
            <button
              onClick={() => copyToClipboard(currentTab?.content || '')}
              className={`px-3 py-1 ${
                copyStatus === 'copied' 
                  ? 'bg-green-500' 
                  : copyStatus === 'failed' 
                    ? 'bg-red-500' 
                    : 'bg-gray-500'
              } text-white rounded hover:opacity-90 flex items-center`}
            >
              {copyStatus === 'copied' ? 'Copied!' : 'Copy'}
            </button>
            <button
              onClick={autoSave.forceSave}
              className="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 flex items-center"
            >
              Save
            </button>
          </div>

          <div className="flex items-center space-x-4">
            <button
              onClick={uiMethods.toggleSettings}
              className={`p-1 rounded-full ${uiState.showSettings ? 'bg-blue-500 text-white' : ''}`}
              title="Editor Settings"
            >
              <Settings className="h-5 w-5" />
            </button>

            <button
              onClick={() => window.close()}
              className="px-3 py-1 bg-red-500 text-white rounded hover:bg-red-600"
            >
              Close
            </button>
          </div>
        </div>

        {/* Settings Panel */}
        {uiState.showSettings && (
          <SettingsPanel
            isVisible={uiState.showSettings}
            onClose={uiMethods.toggleSettings}
            isDarkTheme={theme.isDark}
            fontSize={uiState.fontSize}
            setFontSize={uiMethods.setFontSize}
            showLineNumbers={uiState.showLineNumbers}
            setShowLineNumbers={uiMethods.toggleLineNumbers}
            isHighlighting={uiState.isHighlighting}
            setIsHighlighting={uiMethods.toggleHighlighting}
            folding={folding.folding}
            toggleFolding={folding.toggleFolding}
            bracketMatching={bracketMatching.bracketMatching}
            toggleBracketMatching={() => bracketMatching.setBracketMatching(prev => !prev)}
            currentTheme={theme.currentTheme}
            availableThemes={['prism', 'okaidia', 'solarizedlight', 'tomorrow', 'dark']}
            changeTheme={changeTheme}
            toggleTheme={toggleTheme}
          />
        )}

        {/* Additional Panels and Components */}
        <ThemeSelector theme={theme} changeTheme={changeTheme} />
        
        {findReplace.visible && (
          <FindReplacePanel
            findReplace={findReplace}
            setFindReplace={setFindReplace}
            findText={(direction) => {
              const result = editorFeatures.findText(
                findReplace.findText, 
                findReplace.matchCase, 
                findReplace.wholeWord,
                direction
              );
              setFindReplace(prev => ({
                ...prev,
                matches: result.matches,
                currentMatch: result.currentMatch
              }));
            }}
            replaceText={(replaceAll) => {
              editorFeatures.replaceText(
                findReplace.findText,
                findReplace.replaceText,
                findReplace.matchCase,
                findReplace.wholeWord,
                replaceAll
              );
            }}
            isDarkTheme={theme.isDark}
          />
        )}

        <StatusBar
          fileName={currentTab?.fileName || ''}
          language={currentLanguage}
          cursorPosition={cursorPosition}
          isDarkTheme={theme.isDark}
          isPythonFile={currentTab?.fileName.endsWith('.py') || false}
          bracketMatching={bracketMatching.bracketMatching}
          autoSaveEnabled={autoSave.autoSave.enabled}
          lastSaved={autoSave.autoSave.lastSaved}
          modifiedSinceLastSave={autoSave.autoSave.lastSaved !== null && currentTab?.content !== currentTab?.lastSavedContent}
          isCollaborative={collaboration.isCollaborationEnabled}
          lastEditBy={currentTab?.lastEditBy || collaboration.lastChangeBy}
          typingUsers={typingIndicator.typingUsers}
          currentUserEmail={currentUserEmail}
        />
      </div>

      {/* Editor Area */}
      <EditorArea
        content={currentTab?.content || ''}
        fontSize={uiState.fontSize}
        showLineNumbers={uiState.showLineNumbers}
        isHighlighting={uiState.isHighlighting}
        highlightedContent={highlightedContent}
        isDarkTheme={theme.isDark}
        folding={folding.folding}
        toggleLineFolding={folding.toggleLineFolding}
        foldableLines={folding.getFoldableLines(currentTab?.content || '')}
        bracketMatching={bracketMatching.bracketMatching}
        matchedBrackets={bracketMatching.matchedBrackets}
        onChange={(newContent) => {
          // First update local state
          editor.handleTabContentChange(newContent);
          
          // Then broadcast the change if collaborative mode is enabled
          // Only send changes that originated locally
          if (collaboration.isCollaborationEnabled && 
              currentTab && 
              !collaboration.isApplyingRemoteChange()) {
            const updatedTab = {
              ...currentTab,
              content: newContent
            };
            collaboration.sendEditorChange(updatedTab);
          }
        }}
        onKeyDown={keyboardShortcuts.handleKeyDown}
        updateCursorPosition={updateCursorPosition}
        renderFoldedContent={folding.renderFoldedContent}
        textareaRef={textareaRef}
        onTyping={typingIndicator.handleTyping}
        typingUsers={typingIndicator.typingUsers}
        currentUserEmail={currentUserEmail}
      />

      {/* Keyboard Shortcuts Help */}
      <KeyboardShortcutsHelp
        isDarkTheme={theme.isDark}
        expanded={uiState.keyboardShortcutsExpanded}
        toggleExpanded={uiMethods.toggleKeyboardShortcuts}
      />

      {/* Debug Panel */}
      {uiState.showDebugPanel && (
        <DebugPanel
          editorState={editor}
          cursorPosition={cursorPosition}
          autoSave={autoSave.autoSave}
          theme={theme}
          folding={folding.folding}
          bracketMatching={bracketMatching.bracketMatching}
          sessionId={sessionId}
        />
      )}
    </div>
  );
}
