import { useCallback } from 'react';
import { EditorTab } from '../types';

interface UseEditorFeaturesProps {
  currentTab: EditorTab | undefined;
  textareaRef: React.RefObject<HTMLTextAreaElement>;
  handleTabContentChange: (content: string) => void;
  updateCursorPosition: () => void;
  isPythonFile: () => boolean;
}

export function useEditorFeatures({
  currentTab,
  textareaRef,
  handleTabContentChange,
  updateCursorPosition,
  isPythonFile
}: UseEditorFeaturesProps) {
  // Escape special characters in regex
  const escapeRegExp = useCallback((string: string) => {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }, []);

  // Find text functionality
  const findText = useCallback((
    findText: string, 
    matchCase: boolean, 
    wholeWord: boolean, 
    direction: 'next' | 'prev' = 'next'
  ) => {
    const textarea = textareaRef.current;
    if (!textarea || !findText || !currentTab) return { matches: 0, currentMatch: 0 };
    
    const content = textarea.value;
    const currentPos = textarea.selectionEnd;
    
    // Create regexp for search
    let flags = 'g';
    if (!matchCase) flags += 'i';
    
    const regex = wholeWord 
      ? new RegExp(`\\b${escapeRegExp(findText)}\\b`, flags)
      : new RegExp(escapeRegExp(findText), flags);
    
    // Find all matches
    const matches = [];
    let match;
    const tempRegex = new RegExp(regex);
    
    while ((match = tempRegex.exec(content)) !== null) {
      matches.push({
        start: match.index,
        end: match.index + match[0].length
      });
      
      // Prevent infinite loop for zero-length matches
      if (tempRegex.lastIndex === match.index) {
        tempRegex.lastIndex++;
      }
    }
    
    if (matches.length === 0) {
      return { matches: 0, currentMatch: 0 };
    }
    
    // Find next match based on direction
    let nextMatchIndex = 0;
    
    if (direction === 'next') {
      // Find the first match after the current position
      nextMatchIndex = matches.findIndex(m => m.start > currentPos);
      if (nextMatchIndex === -1) nextMatchIndex = 0; // Wrap around
    } else {
      // Find the last match before the current position
      for (let i = matches.length - 1; i >= 0; i--) {
        if (matches[i].start < currentPos - 1) {
          nextMatchIndex = i;
          break;
        }
      }
      
      // If no match found before cursor, wrap to the last match
      if (nextMatchIndex === 0 && matches[0].start >= currentPos) {
        nextMatchIndex = matches.length - 1;
      }
    }
    
    // Select the match
    const matchToSelect = matches[nextMatchIndex];
    textarea.focus();
    textarea.setSelectionRange(matchToSelect.start, matchToSelect.end);
    
    // Ensure the match is visible
    textarea.scrollTop = Math.max(0, matchToSelect.start - 200);
    
    return {
      matches: matches.length,
      currentMatch: nextMatchIndex + 1
    };
  }, [textareaRef, currentTab, escapeRegExp]);

  // Replace text functionality
  const replaceText = useCallback((
    findText: string, 
    replaceText: string, 
    matchCase: boolean, 
    wholeWord: boolean, 
    replaceAll: boolean = false
  ) => {
    const textarea = textareaRef.current;
    if (!textarea || !findText || !currentTab) return;
    
    const content = currentTab.content;
    
    // Create regexp for search
    let flags = 'g';
    if (!matchCase) flags += 'i';
    
    const regex = wholeWord 
      ? new RegExp(`\\b${escapeRegExp(findText)}\\b`, flags)
      : new RegExp(escapeRegExp(findText), flags);
    
    if (replaceAll) {
      // Replace all occurrences
      const newContent = content.replace(regex, replaceText);
      handleTabContentChange(newContent);
      return { matches: 0, currentMatch: 0 };
    } else {
      // Replace only the selected occurrence
      const selStart = textarea.selectionStart;
      const selEnd = textarea.selectionEnd;
      
      // Check if the current selection matches the search text
      const selectedText = content.substring(selStart, selEnd);
      if (selectedText.match(new RegExp(regex.source, 'i'))) {
        const newContent = 
          content.substring(0, selStart) + 
          replaceText + 
          content.substring(selEnd);
        
        // Update content
        handleTabContentChange(newContent);
        
        // Position cursor after replacement
        setTimeout(() => {
          textarea.selectionStart = selStart + replaceText.length;
          textarea.selectionEnd = selStart + replaceText.length;
        }, 0);
      }
      
      return { matches: 0, currentMatch: 0 };
    }
  }, [textareaRef, currentTab, handleTabContentChange, escapeRegExp]);

  // Duplicate line functionality
  const duplicateLine = useCallback(() => {
    const textarea = textareaRef.current;
    if (!textarea || !currentTab) return;
    
    const content = currentTab.content;
    const cursorPos = textarea.selectionStart;
    
    // Find the line start
    const lineStart = content.lastIndexOf('\n', cursorPos - 1) + 1;
    
    // Find the line end
    const lineEnd = content.indexOf('\n', cursorPos);
    const actualLineEnd = lineEnd === -1 ? content.length : lineEnd;
    
    // Get the current line
    const currentLine = content.substring(lineStart, actualLineEnd);
    
    // Create new content with duplicated line
    const newContent = 
      content.substring(0, actualLineEnd) + 
      '\n' + 
      currentLine + 
      content.substring(actualLineEnd);
    
    // Update content
    handleTabContentChange(newContent);
    
    // Position cursor at the start of the duplicated line
    setTimeout(() => {
      const newPos = actualLineEnd + 1;
      textarea.selectionStart = textarea.selectionEnd = newPos;
      updateCursorPosition();
    }, 0);
  }, [textareaRef, currentTab, handleTabContentChange, updateCursorPosition]);

  // Indentation functionality
  const indentSelection = useCallback((direction: 'increase' | 'decrease') => {
    const textarea = textareaRef.current;
    if (!textarea || !currentTab) return;
    
    const content = currentTab.content;
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    
    const selectedText = content.substring(start, end);
    const hasMultipleLines = selectedText.includes('\n');
    
    if (hasMultipleLines) {
      // Multi-line selection - indent each line
      const lines = selectedText.split('\n');
      const modifiedLines = lines.map(line => {
        if (direction === 'increase') {
          return '  ' + line;
        } else { // decrease
          return line.startsWith('  ') ? line.substring(2) : line;
        }
      });
      
      const newText = modifiedLines.join('\n');
      const newContent = content.substring(0, start) + newText + content.substring(end);
      
      // Update content
      handleTabContentChange(newContent);
      
      // Restore selection
      setTimeout(() => {
        textarea.selectionStart = start;
        textarea.selectionEnd = start + newText.length;
        updateCursorPosition();
      }, 0);
    } else if (direction === 'increase') {
      // Single line or no selection - just add indentation at cursor
      const newContent = content.substring(0, start) + '  ' + content.substring(end);
      
      // Update content
      handleTabContentChange(newContent);
      
      // Position cursor after indentation
      setTimeout(() => {
        textarea.selectionStart = textarea.selectionEnd = start + 2;
        updateCursorPosition();
      }, 0);
    }
  }, [textareaRef, currentTab, handleTabContentChange, updateCursorPosition]);

  // Auto-indent on enter
  const autoIndent = useCallback((content: string, cursorPos: number) => {
    // Extract the current line
    const lineBeforeCursor = content.substring(0, cursorPos).split('\n').pop() || '';
    
    // Extract indentation from the current line
    const match = lineBeforeCursor.match(/^(\s*)/);
    let indentation = match ? match[1] : '';
    
    // For Python, check if line ends with a colon to add additional indent
    if (isPythonFile() && lineBeforeCursor.trim().endsWith(':')) {
      indentation += '    '; // Add 4 spaces for Python
    }
    
    return indentation;
  }, [isPythonFile]);

  return {
    findText,
    replaceText,
    duplicateLine,
    indentSelection,
    autoIndent
  };
}
