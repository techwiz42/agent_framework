// hooks/useBracketMatching.ts
import { useState } from 'react';
import { EditorTab } from '../types';

export function useBracketMatching(
  tabs: EditorTab[], 
  activeTab: number,
  textareaRef?: React.RefObject<HTMLTextAreaElement>
) {
  const [bracketMatching, setBracketMatching] = useState<boolean>(true);
  const [matchedBrackets, setMatchedBrackets] = useState<{start: number, end: number} | null>(null);

  // Bracket matching detection
  const updateBracketMatching = (cursorPos?: number) => {
    if (!bracketMatching || !tabs[activeTab] || !textareaRef?.current) return;
    
    const textarea = textareaRef.current;
    const content = tabs[activeTab].content;
    
    // If cursorPos is not provided, use the textarea selection
    const position = cursorPos !== undefined 
      ? cursorPos 
      : textarea.selectionStart;
    
    // Check character before cursor
    const charBefore = content[position - 1];
    const charAfter = content[position];
    
    const brackets: Record<string, string> = {
      '(': ')',
      '[': ']',
      '{': '}',
      ')': '(',
      ']': '[',
      '}': '{'
    };
    
    // Reset matched brackets
    setMatchedBrackets(null);
    
    // Check if cursor is at a bracket
    const activeBracket = brackets[charBefore] ? charBefore : brackets[charAfter] ? charAfter : null;
    if (!activeBracket) return;
    
    const isClosingBracket = [')', ']', '}'].includes(activeBracket);
    const matchingBracket = brackets[activeBracket];
    const searchPos = isClosingBracket ? position - 1 : position;
    
    // Find matching bracket
    const stack: string[] = [];
    let matchPosition = -1;
    
    if (isClosingBracket) {
      // Search backward for opening bracket
      for (let i = searchPos; i >= 0; i--) {
        const char = content[i];
        if (char === activeBracket) {
          stack.push(char);
        } else if (char === matchingBracket) {
          if (stack.length === 0) {
            matchPosition = i;
            break;
          }
          stack.pop();
        }
      }
    } else {
      // Search forward for closing bracket
      for (let i = searchPos; i < content.length; i++) {
        const char = content[i];
        if (char === activeBracket) {
          stack.push(char);
        } else if (char === matchingBracket) {
          stack.pop();
          if (stack.length === 0) {
            matchPosition = i;
            break;
          }
        }
      }
    }
    
    if (matchPosition >= 0) {
      setMatchedBrackets({
        start: isClosingBracket ? matchPosition : searchPos,
        end: isClosingBracket ? searchPos : matchPosition
      });
    }
  };

  // Auto-complete brackets function
  const autoCompleteBracket = (
    content: string, 
    position: number, 
    openingBracket: string
  ): { newContent: string, newPosition: number } => {
    if (!bracketMatching) {
      return { newContent: content, newPosition: position };
    }
    
    const closingBrackets: Record<string, string> = {
      '(': ')',
      '[': ']',
      '{': '}',
      '"': '"',
      "'": "'"
    };
    
    const closingBracket = closingBrackets[openingBracket];
    if (!closingBracket) {
      return { newContent: content, newPosition: position };
    }
    
    // Check if we're within a word (don't auto-complete in this case)
    const isWithinWord = 
      /\w/.test(content[position - 1] || '') && 
      /\w/.test(content[position] || '');
    
    if (isWithinWord) {
      return { newContent: content, newPosition: position };
    }
    
    // Add the opening and closing brackets
    const newContent = 
      content.substring(0, position) + 
      openingBracket + 
      closingBracket + 
      content.substring(position);
    
    // Place cursor between brackets
    const newPosition = position + 1;
    
    return { newContent, newPosition };
  };

  // Get bracket pairs for highlighting
  const getBracketPairs = (content: string): { start: number, end: number }[] => {
    if (!bracketMatching) return [];
    
    const pairs: { start: number, end: number }[] = [];
    const stack: { char: string, pos: number }[] = [];
    
    for (let i = 0; i < content.length; i++) {
      const char = content[i];
      
      if ('([{'.includes(char)) {
        stack.push({ char, pos: i });
      } else if (')]}'.includes(char)) {
        const matchingOpening = char === ')' ? '(' : char === ']' ? '[' : '{';
        
        // Find matching opening bracket
        if (stack.length > 0 && stack[stack.length - 1].char === matchingOpening) {
          const openingPos = stack.pop()!.pos;
          pairs.push({ start: openingPos, end: i });
        }
      }
    }
    
    return pairs;
  };

  return {
    bracketMatching,
    matchedBrackets,
    setBracketMatching,
    updateBracketMatching,
    autoCompleteBracket,
    getBracketPairs
  };
}
