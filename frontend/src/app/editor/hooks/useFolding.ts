// hooks/useFolding.ts (Improved code folding)
import { useState, useEffect, useCallback } from 'react';
import { FoldingState, EditorTab } from '../types';

export function useFolding(tabs: EditorTab[], activeTab: number) {
  const [folding, setFolding] = useState<FoldingState>({
    enabled: true,
    foldedLines: new Set<number>()
  });

  // Detect foldable regions (memoized to prevent unnecessary recalculations)
  const detectFoldableRegions = useCallback((content: string): number[] => {
    const lines = content.split('\n');
    const foldableLines: number[] = [];
    
    for (let i = 0; i < lines.length - 1; i++) {
      const currentLine = lines[i];
      const nextLine = lines[i + 1];
      
      const currentIndent = currentLine.match(/^\s*/)?.[0].length || 0;
      const nextIndent = nextLine.match(/^\s*/)?.[0].length || 0;
      
      // Check if next line has more indentation
      if (nextIndent > currentIndent) {
        // Look ahead to find where the block ends
        let endIndex = i + 1;
        while (endIndex < lines.length) {
          const lineIndent = lines[endIndex].match(/^\s*/)?.[0].length || 0;
          if (lineIndent <= currentIndent) break;
          endIndex++;
        }
        
        // Mark the start line as foldable if the block is substantial
        if (endIndex - i > 1) {
          foldableLines.push(i);
        }
      }
    }
    
    return foldableLines;
  }, []);

  // Update foldable regions when content changes
  useEffect(() => {
    if (!folding.enabled || !tabs[activeTab]) return;
    
    const content = tabs[activeTab].content;
    const foldableLines = detectFoldableRegions(content);
    
    console.log('Foldable lines detected:', foldableLines);
    
    // Remove folded lines that are no longer valid
    setFolding(prev => {
      const newFoldedLines = new Set<number>();
      prev.foldedLines.forEach(line => {
        if (foldableLines.includes(line)) {
          newFoldedLines.add(line);
        }
      });
      
      return {
        ...prev,
        foldedLines: newFoldedLines
      };
    });
  }, [tabs, activeTab, folding.enabled, detectFoldableRegions]);

  // Toggle code folding on/off
  const toggleFolding = useCallback(() => {
    console.log('Toggling folding', folding.enabled);
    setFolding(prev => ({
      ...prev,
      enabled: !prev.enabled,
      // Clear folded lines when disabling
      foldedLines: new Set()
    }));
  }, [folding.enabled]);

  // Toggle folding for a specific line
  const toggleLineFolding = useCallback((lineNumber: number) => {
    console.log(`Attempting to toggle folding for line ${lineNumber}`);
    
    setFolding(prev => {
      const newFoldedLines = new Set(prev.foldedLines);
      
      if (newFoldedLines.has(lineNumber)) {
        console.log(`Unfolding line ${lineNumber}`);
        newFoldedLines.delete(lineNumber);
      } else {
        console.log(`Folding line ${lineNumber}`);
        newFoldedLines.add(lineNumber);
      }
      
      console.log('New folded lines:', Array.from(newFoldedLines));
      
      return {
        ...prev,
        foldedLines: newFoldedLines
      };
    });
  }, []);

  // Render the folded content - hide folded regions in the displayed content
  const renderFoldedContent = useCallback((content: string): string => {
    if (!folding.enabled || folding.foldedLines.size === 0) return content;
    
    console.log('Rendering folded content. Folded lines:', Array.from(folding.foldedLines));
    
    const lines = content.split('\n');
    const visibleLines: string[] = [];
    
    for (let i = 0; i < lines.length; i++) {
      // If this line is a fold start, add the first line and a fold indicator
      if (folding.foldedLines.has(i)) {
        // Find the end of the foldable block
        let endIndex = i + 1;
        const baseIndent = lines[i].match(/^\s*/)?.[0].length || 0;
        
        while (endIndex < lines.length) {
          const lineIndent = lines[endIndex].match(/^\s*/)?.[0].length || 0;
          if (lineIndent <= baseIndent) break;
          endIndex++;
        }
        
        // Add the first line of the block
        visibleLines.push(lines[i]);
        
        // Add a fold indicator
        visibleLines.push(`${' '.repeat(baseIndent)}... (${endIndex - i} lines folded)`);
        
        // Skip to the end of the folded block
        i = endIndex - 1;
      } else {
        // Add regular lines that aren't folded
        visibleLines.push(lines[i]);
      }
    }
    
    return visibleLines.join('\n');
  }, [folding]);

  // Get all foldable line numbers for the current content
  const getFoldableLines = useCallback((content: string): number[] => {
    return detectFoldableRegions(content);
  }, [detectFoldableRegions]);

  return {
    folding,
    toggleFolding,
    toggleLineFolding,
    renderFoldedContent,
    getFoldableLines
  };
}
