import { useState, useCallback } from 'react';

type CopyStatus = 'idle' | 'copied' | 'failed';

interface CopyPasteOptions {
  /** 
   * Optional callback to be called after successful copy
   */
  onCopySuccess?: () => void;
  
  /** 
   * Optional callback to be called after copy failure
   */
  onCopyFailure?: (error?: Error) => void;
  
  /** 
   * Duration to show copy status (in milliseconds)
   * @default 2000
   */
  statusDuration?: number;
}

export function useCopyPaste(options: CopyPasteOptions = {}) {
  const [copyStatus, setCopyStatus] = useState<CopyStatus>('idle');
  
  const {
    onCopySuccess,
    onCopyFailure,
    statusDuration = 2000
  } = options;

  const copyToClipboard = useCallback(async (content: string) => {
    try {
      // Try using the modern clipboard API first
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(content);
        setCopyStatus('copied');
        onCopySuccess?.();
      } else {
        // Fallback method using execCommand
        const textarea = document.createElement('textarea');
        textarea.value = content;
        textarea.style.position = 'fixed';
        document.body.appendChild(textarea);
        textarea.focus();
        textarea.select();
        
        const successful = document.execCommand('copy');
        document.body.removeChild(textarea);
        
        if (successful) {
          setCopyStatus('copied');
          onCopySuccess?.();
        } else {
          throw new Error('Copy command failed');
        }
      }
    } catch (err) {
      console.error('Failed to copy:', err);
      setCopyStatus('failed');
      onCopyFailure?.(err instanceof Error ? err : new Error('Unknown copy error'));
    } finally {
      // Reset status after specified duration
      const timer = setTimeout(() => {
        setCopyStatus('idle');
      }, statusDuration);

      // Cleanup function to clear timeout
      return () => clearTimeout(timer);
    }
  }, [onCopySuccess, onCopyFailure, statusDuration]);

  const resetCopyStatus = useCallback(() => {
    setCopyStatus('idle');
  }, []);

  return {
    /**
     * Current copy status
     */
    copyStatus,
    
    /**
     * Method to copy content to clipboard
     */
    copyToClipboard,
    
    /**
     * Method to manually reset copy status
     */
    resetCopyStatus
  };
}
