import { useState, useEffect, useCallback } from 'react';
import Prism from 'prismjs';
import { FILE_TYPE_MAP } from '../types';

// Preload Prism language components
import 'prismjs/components/prism-javascript';
import 'prismjs/components/prism-python';
import 'prismjs/components/prism-jsx';
import 'prismjs/components/prism-typescript';
import 'prismjs/components/prism-css';
import 'prismjs/components/prism-markup'; // HTML
import 'prismjs/components/prism-tsx';       // TypeScript JSX
import 'prismjs/components/prism-json';      // JSON
import 'prismjs/components/prism-java';      // Java
import 'prismjs/components/prism-scala';
import 'prismjs/components/prism-go';        // Go
import 'prismjs/components/prism-ruby';      // Ruby
import 'prismjs/components/prism-rust';      // Rust
import 'prismjs/components/prism-c';         // C
import 'prismjs/components/prism-cpp';       // C++
import 'prismjs/components/prism-csharp';    // C#
import 'prismjs/components/prism-r';        // R
import 'prismjs/components/prism-matlab';   // MATLAB
import 'prismjs/components/prism-bash';      // Bash/Shell
interface UseSyntaxHighlightingOptions {
  /**
   * Content to highlight
   */
  content: string;
  
  /**
   * Filename to determine language
   */
  fileName: string;
  
  /**
   * Whether highlighting is enabled
   */
  isHighlighting?: boolean;
}

export function useSyntaxHighlighting({
  content,
  fileName,
  isHighlighting = true
}: UseSyntaxHighlightingOptions) {
  const [highlightedContent, setHighlightedContent] = useState('');

  // Determine language based on file extension
  const getCurrentLanguage = useCallback(() => {
    const extension = fileName.split('.').pop()?.toLowerCase() || '';
    return FILE_TYPE_MAP[extension] || 'markup';
  }, [fileName]);

  // Highlight content
  useEffect(() => {
    if (!isHighlighting) {
      setHighlightedContent('');
      return;
    }
    
    try {
      const language = getCurrentLanguage();
      
      if (Prism.languages[language]) {
        const highlighted = Prism.highlight(
          content || '', 
          Prism.languages[language], 
          language
        );
        setHighlightedContent(highlighted);
      } else {
        // Fallback to plain text with HTML escaping
        setHighlightedContent(
          content
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;')
        );
      }
    } catch (e) {
      console.error('Syntax highlighting error:', e);
      setHighlightedContent(
        content
          .replace(/&/g, '&amp;')
          .replace(/</g, '&lt;')
          .replace(/>/g, '&gt;')
      );
    }
  }, [content, isHighlighting, getCurrentLanguage]);

  return {
    /**
     * Highlighted content as HTML string
     */
    highlightedContent,
    
    /**
     * Current language detected for highlighting
     */
    currentLanguage: getCurrentLanguage()
  };
}
