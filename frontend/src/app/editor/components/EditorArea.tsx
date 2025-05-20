// components/EditorArea.tsx (With typing indicators)
import React, { useRef, useEffect } from 'react';
import { ChevronRight, ChevronDown } from 'lucide-react';
import { FoldingState } from '../types';
import { TypingIndicator, TypingUser } from './TypingIndicator';

interface EditorAreaProps {
  content: string;
  fontSize: number;
  showLineNumbers: boolean;
  isHighlighting: boolean;
  highlightedContent: string;
  isDarkTheme: boolean;
  folding: FoldingState;
  toggleLineFolding: (lineNumber: number) => void;
  foldableLines: number[];
  bracketMatching: boolean;
  matchedBrackets: { start: number, end: number } | null;
  onChange: (content: string) => void;
  onKeyDown: (e: React.KeyboardEvent<HTMLTextAreaElement>) => void;
  updateCursorPosition: () => void;
  renderFoldedContent: (content: string) => string;
  textareaRef: React.RefObject<HTMLTextAreaElement>;
  onTyping?: () => void;
  typingUsers?: TypingUser[];
  currentUserEmail?: string;
}

export function EditorArea({
  content,
  fontSize,
  showLineNumbers,
  isHighlighting,
  highlightedContent,
  isDarkTheme,
  folding,
  toggleLineFolding,
  foldableLines,
  bracketMatching,
  matchedBrackets,
  onChange,
  onKeyDown,
  updateCursorPosition,
  renderFoldedContent,
  textareaRef,
  onTyping,
  typingUsers = [],
  currentUserEmail = ''
}: EditorAreaProps) {
  const highlightedRef = useRef<HTMLPreElement>(null);
  const editorContainerRef = useRef<HTMLDivElement>(null);
  
  // Synchronize textarea scrolling with highlighted content
  useEffect(() => {
    const textarea = textareaRef.current;
    const highlighted = highlightedRef.current;
    
    if (!textarea || !highlighted) return;
    
    const syncScroll = () => {
      highlighted.scrollTop = textarea.scrollTop;
      highlighted.scrollLeft = textarea.scrollLeft;
    };
    
    textarea.addEventListener('scroll', syncScroll);
    
    return () => {
      textarea.removeEventListener('scroll', syncScroll);
    };
  }, [textareaRef]);
  
  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    onChange(e.target.value);
    updateCursorPosition();
    
    // Trigger typing indicator
    if (onTyping) {
      onTyping();
    }
  };
  
  // Fixed bracket highlight calculation
  const getBracketHighlightElements = () => {
    if (!bracketMatching || !matchedBrackets || !textareaRef.current || !editorContainerRef.current) {
      return null;
    }
    
    const textarea = textareaRef.current;
    
    // Get the textarea's padding
    const paddingTop = parseInt(getComputedStyle(textarea).paddingTop);
    const paddingLeft = parseInt(getComputedStyle(textarea).paddingLeft);
    
    // Function to calculate position of a character
    const calculateCharPosition = (charIndex: number) => {
      // Find the line number and column for this index
      const textBeforeChar = content.substring(0, charIndex);
      const lines = textBeforeChar.split('\n');
      const lineIndex = lines.length - 1;
      const column = lines[lineIndex].length;
      
      // Calculate position
      const lineHeight = fontSize * 1.5;
      const charWidth = fontSize * 0.6; // Approximate width for monospace font
      
      return {
        top: lineIndex * lineHeight + paddingTop,
        left: column * charWidth + paddingLeft
      };
    };
    
    // Calculate positions for both brackets
    const startPos = calculateCharPosition(matchedBrackets.start);
    const endPos = calculateCharPosition(matchedBrackets.end);
    
    return (
      <>
        <div
          className="absolute z-5 pointer-events-none"
          style={{
            top: `${startPos.top}px`,
            left: `${startPos.left}px`,
            width: `${fontSize * 0.6}px`,
            height: `${fontSize * 1.5}px`,
            backgroundColor: 'rgba(100, 100, 255, 0.3)',
            border: '1px solid rgba(100, 100, 255, 0.7)',
            borderRadius: '2px'
          }}
        />
        <div
          className="absolute z-5 pointer-events-none"
          style={{
            top: `${endPos.top}px`,
            left: `${endPos.left}px`,
            width: `${fontSize * 0.6}px`,
            height: `${fontSize * 1.5}px`,
            backgroundColor: 'rgba(100, 100, 255, 0.3)',
            border: '1px solid rgba(100, 100, 255, 0.7)',
            borderRadius: '2px'
          }}
        />
      </>
    );
  };
  
  return (
    <div className="flex-grow relative">
      <div className={`w-full h-full flex ${isDarkTheme ? 'bg-gray-900' : 'bg-white'} border shadow-inner`}>
        {/* Line numbers column */}
        {showLineNumbers && (
          <div className={`${isDarkTheme ? 'bg-gray-800 text-gray-400' : 'bg-gray-100 text-gray-500'} text-right pr-2 pt-4 overflow-hidden select-none`} style={{ width: '50px' }}>
            {content.split('\n').map((_, i) => (
              <div
                key={i}
                className="flex items-center justify-end"
                style={{
                  fontSize: `${fontSize}px`,
                  lineHeight: '1.5',
                  height: `${fontSize * 1.5}px`
                }}
              >
                {folding.enabled && foldableLines.includes(i) && (
                  <button
                    className="mr-1 opacity-50 hover:opacity-100 focus:outline-none"
                    onClick={() => {
                      console.log(`Clicking fold button for line ${i}`);
                      toggleLineFolding(i);
                    }}
                    style={{
                      width: '12px',
                      height: '12px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}
                  >
                    {folding.foldedLines.has(i) ? 
                      <ChevronRight className="w-3 h-3" /> : 
                      <ChevronDown className="w-3 h-3" />
                    }
                  </button>
                )}
                <span className="mr-1">{i + 1}</span>
              </div>
            ))}
          </div>
        )}

        {/* Editor container */}
        <div className="flex-grow relative overflow-hidden" ref={editorContainerRef}>
          {/* Typing indicators */}
          {typingUsers.length > 0 && currentUserEmail && (
            <TypingIndicator 
              typingUsers={typingUsers} 
              currentUserEmail={currentUserEmail}
              isDarkTheme={isDarkTheme}
            />
          )}
          
          {/* Bracket matching highlights */}
          {getBracketHighlightElements()}
          
          {/* Highlighted code (read-only overlay) */}
          {isHighlighting && (
            <pre
              ref={highlightedRef}
              className="absolute top-0 left-0 w-full h-full overflow-auto p-4 pointer-events-none m-0 z-10"
              style={{
                fontSize: `${fontSize}px`,
                lineHeight: '1.5',
                tabSize: 2
              }}
              dangerouslySetInnerHTML={{
                __html: highlightedContent || ''
              }}
            />
          )}

          {/* Editable textarea (under the overlay) */}
          <textarea
            ref={textareaRef}
            value={folding.enabled ? renderFoldedContent(content) : content}
            onChange={handleChange}
            onKeyDown={onKeyDown}
            onClick={updateCursorPosition}
            onKeyUp={updateCursorPosition}
            className={`absolute top-0 left-0 w-full h-full p-4 font-mono border-none resize-none outline-none ${
              isDarkTheme ? 'bg-gray-900 caret-white' : ''
            }`}
            spellCheck="false"
            style={{
              fontSize: `${fontSize}px`,
              lineHeight: '1.5',
              color: isHighlighting ? 'transparent' : 'inherit',
              caretColor: isDarkTheme ? 'white' : 'black', // Always show the cursor
              background: 'transparent',
              tabSize: 2
            }}
          />
        </div>
      </div>
    </div>
  );
}
