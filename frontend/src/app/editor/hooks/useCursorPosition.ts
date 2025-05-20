import { useState, useCallback } from 'react';
import { CursorPosition } from '../types';

interface UseCursorPositionOptions {
  /**
   * Optional callback to be called when cursor position changes
   */
  onPositionChange?: (position: CursorPosition) => void;
  
  /**
   * Optional callback for bracket matching
   */
  onBracketMatching?: (cursorPos: number) => void;
}

export function useCursorPosition(
  textareaRef: React.RefObject<HTMLTextAreaElement>, 
  options: UseCursorPositionOptions = {}
) {
  const [cursorPosition, setCursorPosition] = useState<CursorPosition>({ 
    line: 1, 
    column: 1 
  });

  const updateCursorPosition = useCallback(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;
    
    const cursorPos = textarea.selectionStart;
    const value = textarea.value;
    
    // Find line and column
    let line = 1;
    let column = 1;
    
    for (let i = 0; i < cursorPos; i++) {
      if (value[i] === '\n') {
        line++;
        column = 1;
      } else {
        column++;
      }
    }
    
    const newPosition = { line, column };
    
    // Update state
    setCursorPosition(newPosition);
    
    // Call optional onPositionChange callback
    options.onPositionChange?.(newPosition);
    
    // Call optional bracket matching
    if (options.onBracketMatching) {
      options.onBracketMatching(cursorPos);
    }
  }, [textareaRef, options]);

  return {
    /**
     * Current cursor position
     */
    cursorPosition,
    
    /**
     * Method to update cursor position
     */
    updateCursorPosition
  };
}
