// hooks/useKeyboardShortcuts.ts
import { useCallback, useRef } from 'react';
import { EditorTab } from '../types';

type ShortcutHandler = (e: React.KeyboardEvent<HTMLTextAreaElement>) => void;

interface ShortcutHandlers {
  save: () => void;
  find: () => void;
  format?: () => void;
  goToLine: (line?: number) => void;
  duplicateLine: () => void;
  toggleComment?: () => void;
  indentSelection: (direction: 'increase' | 'decrease') => void;
}

export function useKeyboardShortcuts(
  tabs: EditorTab[],
  activeTab: number,
  updateTabs: (newTabs: EditorTab[]) => void,
  textareaRef: React.RefObject<HTMLTextAreaElement>,
  handlers: ShortcutHandlers
) {
  // Keep track of the last cursor position after operations
  const lastSelectionRef = useRef<{start: number, end: number}>({start: 0, end: 0});
  
  // Parse current line details
  const getCurrentLineDetails = useCallback(() => {
    const textarea = textareaRef.current;
    if (!textarea || !tabs[activeTab]) return null;
    
    const value = textarea.value;
    const cursorPos = textarea.selectionStart;
    
    // Find the start of the current line
    const lineStart = value.lastIndexOf('\n', cursorPos - 1) + 1;
    
    // Find the end of the current line
    const lineEnd = value.indexOf('\n', cursorPos);
    const actualLineEnd = lineEnd === -1 ? value.length : lineEnd;
    
    // Extract the current line content
    const currentLine = value.substring(lineStart, actualLineEnd);
    
    // Extract indentation
    const indentation = currentLine.match(/^(\s*)/)?.[0] || '';
    
    return {
      lineStart,
      lineEnd: actualLineEnd,
      currentLine,
      indentation,
      value,
      cursorPos
    };
  }, [textareaRef, tabs, activeTab]);
  
  // Handle keyboard shortcuts
  const handleKeyDown: ShortcutHandler = useCallback((e) => {
    const textarea = textareaRef.current;
    if (!textarea || !tabs[activeTab]) return;
    
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    
    // Store selection for future reference
    lastSelectionRef.current = {start, end};
    
    // Check for key combinations (Ctrl or Cmd)
    const isCtrlOrCmd = e.ctrlKey || e.metaKey;
    
    if (isCtrlOrCmd) {
      // Ctrl+S or Command+S - Save
      if (e.key === 's') {
        e.preventDefault();
        handlers.save();
        return;
      }
      
      // Ctrl+F or Command+F - Find
      if (e.key === 'f') {
        e.preventDefault();
        handlers.find();
        return;
      }
      
      // Ctrl+Shift+F or Command+Shift+F - Format code
      if (e.key === 'F' && e.shiftKey && handlers.format) {
        e.preventDefault();
        handlers.format();
        return;
      }
      
      // Ctrl+G or Command+G - Go to line
      if (e.key === 'g') {
        e.preventDefault();
        handlers.goToLine();
        return;
      }
      
      // Ctrl+/ or Command+/ - Toggle comment
      if (e.key === '/' && handlers.toggleComment) {
        e.preventDefault();
        handlers.toggleComment();
        return;
      }
      
      // Ctrl+D or Command+D - Duplicate line
      if (e.key === 'd') {
        e.preventDefault();
        handlers.duplicateLine();
        return;
      }
      
      // Ctrl+[ or Command+[ - Decrease indent
      if (e.key === '[') {
        e.preventDefault();
        handlers.indentSelection('decrease');
        return;
      }
      
      // Ctrl+] or Command+] - Increase indent
      if (e.key === ']') {
        e.preventDefault();
        handlers.indentSelection('increase');
        return;
      }
    }
  }, [textareaRef, tabs, activeTab, handlers]);
  
  // Implementation of indentation logic
  const indentSelection = useCallback((direction: 'increase' | 'decrease') => {
    const textarea = textareaRef.current;
    if (!textarea || !tabs[activeTab]) return;
    
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const value = textarea.value;
    
    const selectedText = value.substring(start, end);
    const hasMultipleLines = selectedText.includes('\n');
    
    if (hasMultipleLines) {
      // Multi-line selection - indent each line
      const lines = selectedText.split('\n');
      const modifiedLines = lines.map(line => {
        if (direction === 'increase') {
          return '  ' + line;
        } else {
          // Decrease indentation
          return line.startsWith('  ') ? line.substring(2) : line;
        }
      });
      
      const newText = modifiedLines.join('\n');
      const newValue = value.substring(0, start) + newText + value.substring(end);
      
      // Update content
      const newTabs = [...tabs];
      newTabs[activeTab].content = newValue;
      updateTabs(newTabs);
      
      // Restore selection
      setTimeout(() => {
        textarea.selectionStart = start;
        textarea.selectionEnd = start + newText.length;
        
        // Update last selection reference
        lastSelectionRef.current = {
          start: textarea.selectionStart,
          end: textarea.selectionEnd
        };
      }, 0);
    } else if (direction === 'increase') {
      // No selection or single line - add indentation at cursor
      const newValue = value.substring(0, start) + '  ' + value.substring(end);
      
      // Update content
      const newTabs = [...tabs];
      newTabs[activeTab].content = newValue;
      updateTabs(newTabs);
      
      // Set cursor after indentation
      setTimeout(() => {
        textarea.selectionStart = textarea.selectionEnd = start + 2;
        
        // Update last selection reference
        lastSelectionRef.current = {
          start: textarea.selectionStart,
          end: textarea.selectionEnd
        };
      }, 0);
    }
  }, [textareaRef, tabs, activeTab, updateTabs]);
  
  // Implement duplicate line functionality
  const duplicateLine = useCallback(() => {
    const lineDetails = getCurrentLineDetails();
    if (!lineDetails || !textareaRef.current) return;
    
    const { lineStart, lineEnd, currentLine, value } = lineDetails;
    
    // Create new content with duplicated line
    const newValue = 
      value.substring(lineStart, lineEnd) + 
      '\n' + 
      currentLine + 
      value.substring(lineEnd);
    
    // Update tabs
    const newTabs = [...tabs];
    newTabs[activeTab].content = newValue;
    updateTabs(newTabs);
    
    // Position cursor at the start of the duplicated line
    setTimeout(() => {
      const textarea = textareaRef.current;
      if (!textarea) return;
      
      const newPos = lineEnd + 1;
      textarea.selectionStart = textarea.selectionEnd = newPos;
      
      // Update last selection reference
      lastSelectionRef.current = {
        start: newPos,
        end: newPos
      };
    }, 0);
  }, [getCurrentLineDetails, textareaRef, tabs, activeTab, updateTabs]);
  
  // Go to specific line number
  const goToLine = useCallback((targetLine?: number) => {
    const textarea = textareaRef.current;
    if (!textarea || !tabs[activeTab]) return;
    
    // If no line number provided, prompt user
    if (targetLine === undefined) {
      const lineNumberStr = prompt('Go to line:');
      if (!lineNumberStr || isNaN(parseInt(lineNumberStr))) return;
      targetLine = parseInt(lineNumberStr);
    }
    
    // Ensure line number is valid
    const lines = textarea.value.split('\n');
    if (targetLine < 1 || targetLine > lines.length) {
      alert(`Line number must be between 1 and ${lines.length}`);
      return;
    }
    
    // Convert to 0-based index
    const lineIndex = targetLine - 1;
    
    // Calculate position of the target line
    let position = 0;
    for (let i = 0; i < lineIndex; i++) {
      position += lines[i].length + 1; // +1 for the newline character
    }
    
    // Set cursor position
    textarea.focus();
    textarea.selectionStart = textarea.selectionEnd = position;
    
    // Ensure the line is visible
    const lineHeight = 20; // Approximate line height in pixels
    textarea.scrollTop = lineIndex * lineHeight;
    
    // Update last selection reference
    lastSelectionRef.current = {
      start: position,
      end: position
    };
  }, [textareaRef, tabs, activeTab]);
  
  // Create compound handlers that combine hooks with provided handlers
  const shortcutHandlers = {
    handleKeyDown,
    duplicateLine,
    goToLine,
    indentSelection
  };
  
  return shortcutHandlers;
}
