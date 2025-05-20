// @/app/conversations/[id]/components/MessageItem.tsx
import React, { useEffect, useRef, useState } from 'react';
import { Message } from '../types/message.types';
import { DownloadButton } from './DownloadButton';
import { Copy } from 'lucide-react';
import { useToast } from '@/components/ui/use-toast';
import { useAuth } from '@/context/AuthContext';
import FileDisplay from '@/app/conversations/[id]/components/FileDisplay';

// Define an enhanced interface for the Message type to include all needed properties
interface EnhancedMessage extends Message {
  message_info?: {
    is_file?: boolean;
    file_name?: string;
    file_type?: string;
    file_size?: number;
    is_private?: boolean;
    is_streaming?: boolean;  // New flag to indicate streaming
    [key: string]: unknown;
  };
  agent_type?: string;
  is_streaming?: boolean;    // Top-level flag for easier access
  streaming_content?: string; // Current streamed content
}

declare global {
  interface Window {
    editorWindowRef?: Window | null;
  }
}

// Create a type guard function
function hasMessageInfo(message: Message): message is EnhancedMessage {
  return 'message_info' in message && message.message_info !== undefined;
}

interface Props {
  message: Message;
  formatDate: (date: string) => string;
  responseTime?: string;
  isStreaming?: boolean;
  streamingContent?: string;
}

export const formatAgentName = (agentType?: string, email?: string) => {
  if (!agentType) {
    return email?.split('@')[0].toUpperCase() || 'Unknown';
  }

  return agentType
    .split('_')
    .map(word => word.charAt(0) + word.slice(1).toLowerCase())
    .join(' ')
    .replace(/\s?Agent$/, '');
};

const MessageItem: React.FC<Props> = ({ 
  message, 
  formatDate, 
  responseTime,
  isStreaming = false,
  streamingContent = ''
}) => {
  const { toast } = useToast();
  const { user, token } = useAuth();
  const [editableContent, setEditableContent] = useState<{
    content: string;
    fileName: string;
    fileType: string;
  } | null>(null);
  const contentRef = useRef<HTMLDivElement>(null);
  
  // Cast message to EnhancedMessage for easier access to optional properties
  const enhancedMessage = message as EnhancedMessage;
  
  // Use passed streaming content or from message if available
  const currentStreamingContent = streamingContent || enhancedMessage.streaming_content || '';
  const messageIsStreaming = isStreaming || enhancedMessage.is_streaming || 
    (hasMessageInfo(message) && message.message_info?.is_streaming);

  useEffect(() => {
    if (contentRef.current) {
      const editableScript = contentRef.current.querySelector('script[type="application/vnd.ant.editable"]');
      if (editableScript) {
        try {
          const editableData = JSON.parse(editableScript.textContent || '');
          console.log("Found editable script data:", editableData);
          setEditableContent(editableData);
          // Remove the script tag after processing
          editableScript.remove();
        } catch (error) {
          console.error("Error parsing editable script content:", error);
        }
      }
    }
  }, [message.content]);

  const detectFileType = (content: string, messageInfo?: Record<string, unknown>): string => {
    // First check message_info if available
    if (messageInfo?.file_type) {
      return messageInfo.file_type as string;
    }

    // Then check for code-monkey-response
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = content;
    
    const codeElement = tempDiv.querySelector('.code-monkey-response pre code');
    if (codeElement) {
      const languageClass = Array.from(codeElement.classList).find(cls => cls.startsWith('language-'));
      if (languageClass) {
        const language = languageClass.replace('language-', '');
        const langToExtMap: {[key: string]: string} = {
            'python': 'py',
            'javascript': 'js',
            'typescript': 'ts',
            'typescriptreact': 'tsx',
            'javascriptreact': 'jsx',
            'scala': 'scala',
            'lisp': 'lisp',
            'clojure': 'clj',
            'scheme': 'scm',
            'haskell': 'hs',
            'java': 'java',
            'c': 'c',
            'cpp': 'cpp',
            'csharp': 'cs',
            'php': 'php',
            'ruby': 'rb',
            'swift': 'swift',
            'kotlin': 'kt',
            'go': 'go',
            'rust': 'rs',
            'sql': 'sql',
            'html': 'html',
            'css': 'css',
            'xml': 'xml',
            'json': 'json',
            'yaml': 'yml',
            'markdown': 'md'
          };
        return langToExtMap[language] || language;
      }
    }
    
    return 'txt';
  };

  const extractCodeContent = (originalContent: string) => {
    console.log("Extracting code content from:", originalContent.substring(0, 100) + "...");
    
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = originalContent;
    
    // Try to extract from editable script
    const codeScript = tempDiv.querySelector('script[type="application/vnd.ant.editable"]');
    if (codeScript) {
      try {
        const editableData = JSON.parse(codeScript.textContent || '{}');
        console.log("Found editable script, content length:", editableData.content?.length);
        return editableData.content || originalContent;
      } catch (error) {
        console.error("Error parsing script content:", error);
      }
    }

    // Try to extract from code monkey response
    const codeElement = tempDiv.querySelector('.code-monkey-response pre code');
    if (codeElement) {
      console.log("Found code element, content length:", codeElement.textContent?.length);
      return codeElement.textContent || originalContent;
    }

    console.log("No specific code format found, returning original content");
    return originalContent;
  };

  const getMessageClasses = () => {
    const baseClasses = "rounded-lg px-4 py-3 max-w-[70%] relative text-sm break-all";
    return message.sender.type === 'user'
      ? `${baseClasses} bg-blue-500 text-white ml-auto` 
      : `${baseClasses} bg-green-300 text-gray-900 border border-blue-300`;
  };

  // Check if the string is HTML
  const isHTML = (str: string) => {
    return /<[a-z][\s\S]*>/i.test(str);
  };
  
  // Process LaTeX-like math expressions
  const processMathExpressions = (content: string) => {
    // Replace \[ ... \] with proper math display
    const displayMathRegex = /\\[\[](.+?)\\[\]]/g;
    const processedContent = content.replace(displayMathRegex, (match, formula) => {
      return `<div class="math-display">${formula}</div>`;
    });
    
    return processedContent;
  };
  
  // Check if content might be Markdown (with some basic markers)
  const isMarkdown = (text: string): boolean => {
    // Check for common markdown patterns
    const markdownPatterns = [
      /^#{1,6}\s/, // Headers
      /\*\*.*\*\*/, // Bold
      /\*.*\*/, // Italic 
      /`.*`/, // Inline code
      /```[\s\S]*```/, // Code blocks
      /\[.*\]\(.*\)/, // Links
      /^[-*+]\s/, // Unordered lists
      /^\d+\.\s/, // Ordered lists
      /^>\s/, // Blockquotes
      /^---$/ // Horizontal rules
    ];
    
    return markdownPatterns.some(pattern => pattern.test(text));
  };
  
  // Convert markdown to HTML
  const renderMarkdown = (text: string): string => {
    let html = text;

    // Convert headers
    html = html.replace(/^#{6}\s+(.+)$/gm, '<h6>$1</h6>');
    html = html.replace(/^#{5}\s+(.+)$/gm, '<h5>$1</h5>');
    html = html.replace(/^#{4}\s+(.+)$/gm, '<h4>$1</h4>');
    html = html.replace(/^#{3}\s+(.+)$/gm, '<h3>$1</h3>');
    html = html.replace(/^#{2}\s+(.+)$/gm, '<h2>$1</h2>');
    html = html.replace(/^#{1}\s+(.+)$/gm, '<h1>$1</h1>');

    // Convert bold text
    html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    
    // Convert italic text
    html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');
    html = html.replace(/_([^_]+)_/g, '<em>$1</em>');

    // Convert code blocks
    html = html.replace(/```([a-zA-Z]*)\n([\s\S]*?)```/g, (match, lang, code) => {
      return `<pre><code class="language-${lang}">${code}</code></pre>`;
    });
    
    // Convert inline code
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

    // Convert links
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, 
      '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');

    // Convert unordered lists
    const ulRegex = /^[\s]*[-*+][\s]+(.*)/gm;
    const ulMatches = html.match(ulRegex);
    if (ulMatches) {
      let inList = false;
      html = html.replace(ulRegex, (match, item) => {
        if (!inList) {
          inList = true;
          return `<ul><li>${item}</li>`;
        }
        return `<li>${item}</li>`;
      });
      // Close any open lists
      if (inList) {
        html = html + '</ul>';
      }
    }
    
    // Convert ordered lists
    const olRegex = /^[\s]*(\d+)\.[\s]+(.*)/gm;
    const olMatches = html.match(olRegex);
    if (olMatches) {
      let inList = false;
      html = html.replace(olRegex, (match, num, item) => {
        if (!inList) {
          inList = true;
          return `<ol><li>${item}</li>`;
        }
        return `<li>${item}</li>`;
      });
      // Close any open lists
      if (inList) {
        html = html + '</ol>';
      }
    }
    
    // Convert blockquotes
    html = html.replace(/^>[\s]+(.*)/gm, '<blockquote>$1</blockquote>');
    
    // Convert horizontal rules
    html = html.replace(/^---$/gm, '<hr/>');
    
    // Convert line breaks
    html = html.replace(/\n/g, '<br/>');
    
    return html;
  };

  const renderContent = () => {
    // Handle streaming content
    if (messageIsStreaming) {
      const cleanedStreamingContent = currentStreamingContent
        .replace(/\[\w+ is thinking\.\.\.\]/g, '')
        .replace(/\[\w+ has completed\]/g, '')
        .replace(/\[Synthesizing collaborative response\.\.\.\]/g, '')
        .replace(/\[TIMEOUT\]/g, '')
        .replace(/\[ERROR\]/g, '')
        .replace(/\[DONE\]/g, '')
        .replace(/\[END\]/g, '')
        .replace(/\[AGENT_COMPLETE\]/g, '')
        .replace(/\n{3,}/g, '\n\n')
        .trim();

      return (
        <div className="whitespace-pre-wrap break-words text-sm">
          {cleanedStreamingContent}
          <span className="typing-indicator inline-block ml-1">
            <span className="dot bg-black"></span>
            <span className="dot bg-black"></span>
            <span className="dot bg-black"></span>
          </span>
        </div>
      );
    }

    // Check for editor invitation
    const enhancedMsg = message as EnhancedMessage;
    const isEditorInvite =
      enhancedMsg.message_info &&
      'editor_invite' in enhancedMsg.message_info &&
      enhancedMsg.message_info.editor_invite === true;

    // Handle editor invitation
    if (isEditorInvite && enhancedMsg.message_info) {
      const editorSession = enhancedMsg.message_info.editor_session as string;
      const conversationId = enhancedMsg.message_info.conversation_id as string;

      return (
        <div className="whitespace-pre-wrap break-words text-sm">
          {message.content}
          <div className="mt-2">
            <button
              onClick={() => {
                window.open(
                  `/editor?session=${editorSession}&conversationId=${conversationId}&token=${encodeURIComponent(token || '')}&email=${encodeURIComponent(user?.email || '')}&name=${encodeURIComponent(user?.username || '')}`,
                  'editor_window',
                  'width=1000,height=800,left=100,top=100,resizable=yes,scrollbars=yes,toolbar=no,menubar=no,location=no,status=yes'
                );
              }}
              className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 flex items-center"
            >
              Join Collaborative Editing Session
            </button>
          </div>
        </div>
      );
    }

    // Handle file content display
    if (hasMessageInfo(message) && message.message_info?.is_file) {
      const detectResult = detectFileType(message.content, message.message_info);

      return (
        <FileDisplay
          content={message.content}
          fileName={message.message_info.file_name}
          isUserMessage={message.sender.type === 'user'}
          onEdit={message.sender.type === 'user' ? () => handleEdit({
            content: message.content,
            fileName: message.message_info?.file_name || `file.${detectResult}`,
            fileType: detectResult
          }) : undefined}
        />
      );
    }

    // Handle editable content
    if (editableContent) {
      return (
        <FileDisplay
          content={editableContent.content}
          fileName={editableContent.fileName}
          isUserMessage={message.sender.type === 'user'}
          onEdit={() => handleEdit(editableContent)}
        />
      );
    }

    // Special handling for document search agent responses
    if (!message.sender.is_owner &&
        (enhancedMessage.agent_type === 'DOCUMENTSEARCH' ||
         message.content.includes('@documentsearch') ||
         message.content.includes('document-link'))) {

      // For document search results, properly render markdown with clickable links
      const content = message.content;

      // Convert markdown to HTML with emphasis on preserving format
      const convertMarkdown = (text: string) => {
        let html = text;

        // Skip HTML conversion if content already contains HTML links
        // This handles the case where backend returns HTML directly
        const containsHtmlLinks = /<a\s+href=/i.test(html);

        if (!containsHtmlLinks) {
          // Convert headers
          html = html.replace(/### ([^\n]+)/g, '<h3>$1</h3>');
          html = html.replace(/## ([^\n]+)/g, '<h2>$1</h2>');
          html = html.replace(/# ([^\n]+)/g, '<h1>$1</h1>');

          // Convert bold text
          html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

          // Convert links - most important for clickability
          html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g,
            '<a href="$2" target="_blank" rel="noopener noreferrer" class="document-link">$1</a>');

          // Convert horizontal rules
          html = html.replace(/^---$/gm, '<hr/>');
          
          // Convert code blocks
          html = html.replace(/```([a-zA-Z]*)\n([\s\S]*?)```/g, (match, lang, code) => {
            return `<pre><code class="language-${lang}">${code}</code></pre>`;
          });
          
          // Convert inline code
          html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
          
          // Convert unordered lists
          const listRegex = /^[\s]*[-*+][\s]+(.*)/gm;
          const listMatches = html.match(listRegex);
          if (listMatches) {
            let inList = false;
            html = html.replace(listRegex, (match, item) => {
              if (!inList) {
                inList = true;
                return `<ul><li>${item}</li>`;
              }
              return `<li>${item}</li>`;
            });
            // Close any open lists
            if (inList) {
              html = html + '</ul>';
            }
          }
        }

        // Always convert line breaks properly
        html = html.replace(/\n/g, '<br/>');

        // Add the italicized note at the bottom if not already present
        if (!html.includes('document-note')) {
          html += '<p class="document-note"><em>Some users may require permission from document owners to view text</em></p>';
        }

        return html;
      };

      // Apply conversion
      const processedContent = convertMarkdown(content);

      return (
        <div
          ref={contentRef}
          className="document-search-results break-all w-full"
          dangerouslySetInnerHTML={{ __html: processedContent }}
          // Remove onClick handler entirely to allow natural link behavior
        />
      );
    }

    // Agent message with code
    if (!message.sender.is_owner && isHTML(message.content)) {
      const detectResult = detectFileType(message.content);
      if (detectResult !== 'txt') {  // Only process if we detected a specific language
        const codeContent = extractCodeContent(message.content);
        return (
          <FileDisplay
            content={codeContent}
            fileName={`code.${detectResult}`}
            isUserMessage={false}
            onEdit={() => handleEdit({
              content: codeContent,
              fileName: `code.${detectResult}`,
              fileType: detectResult
            })}
          />
        );
      }
    }

    // Process and handle HTML content with math expressions
    if (isHTML(message.content)) {
      return <div ref={contentRef} className="overflow-x-auto break-all w-full" dangerouslySetInnerHTML={{ __html: message.content }} />;
    }

    // Process math expressions in non-HTML content
    const processedContent = processMathExpressions(message.content);

    // If processing added HTML, use dangerouslySetInnerHTML
    if (processedContent !== message.content && isHTML(processedContent)) {
      return <div ref={contentRef} className="overflow-x-auto break-all w-full" dangerouslySetInnerHTML={{ __html: processedContent }} />;
    }

    // Handle regular text content
    if (isMarkdown(message.content)) {
      // If content is detected as Markdown, render it as HTML
      return (
        <div 
          ref={contentRef} 
          className="markdown-content whitespace-pre-wrap break-all text-sm w-full"
          dangerouslySetInnerHTML={{ __html: renderMarkdown(message.content) }}
        />
      );
    } else {
      // Regular text that's not Markdown
      return (
        <div ref={contentRef} className="whitespace-pre-wrap break-all text-sm w-full">
          {message.content}
        </div>
      );
    }
  };

  const getInitial = (email: string) => {
    return email ? email[0].toUpperCase() : '?';
  };

  const getAvatarColor = (email: string) => {
    const colors = ['bg-red-500', 'bg-blue-500', 'bg-green-500', 'bg-yellow-500', 'bg-purple-500'];
    const index = email.charCodeAt(0) % colors.length;
    return colors[index]; 
  };

  const handleCopy = async () => {
    // For streaming content, copy what's available so far
    const contentToCopy = messageIsStreaming ? currentStreamingContent : message.content;
    
    // Check if clipboard API is available
    if (typeof navigator !== 'undefined' && navigator.clipboard) {
      try {
        await navigator.clipboard.writeText(contentToCopy);
        toast({
          title: "Copied to clipboard",
          duration: 2000
        });
      } catch (err) {
        console.error('Failed to copy:', err);
        toast({
          title: "Failed to copy", 
          variant: "destructive",
          duration: 2000
        });
      }
    } else {
      // Fallback for environments without clipboard API
      try {
        const textArea = document.createElement('textarea');
        textArea.value = contentToCopy;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);

        toast({
          title: "Copied to clipboard",
          duration: 2000
        });
      } catch (err) {
        console.error('Fallback copy failed:', err);
        toast({
          title: "Failed to copy", 
          variant: "destructive",
          duration: 2000
        });
      }
    }
  };

  // Initialize global window reference if it doesn't exist
  useEffect(() => {
    if (typeof window !== 'undefined' && window.editorWindowRef === undefined) {
      window.editorWindowRef = null;
    }
  }, []);

  const handleEdit = (data: { content: string; fileName: string; fileType: string; }) => {
    console.log("handleEdit called with data:", data);
    
    // Extract code content
    const codeContent = extractCodeContent(data.content);
    console.log("Extracted code content length:", codeContent.length);
    
    const fileType = data.fileType || detectFileType(data.content);
    console.log("Detected fileType:", fileType);
    
    const fileName = data.fileName || `code.${fileType}`;
    console.log("Using fileName:", fileName);
    
    // Get the current conversation ID from the URL
    const pathParts = window.location.pathname.split('/');
    const conversationId = pathParts[pathParts.indexOf('conversations') + 1];
    console.log("Current conversation ID:", conversationId);
    
    // Prepare file data
    const fileData = {
      content: codeContent,
      fileName: fileName, 
      fileType: fileType
    };
    
    // Check if we have a stored reference and if the window is still open
    const hasWindowRef = window.editorWindowRef !== null;
    const windowIsOpen = hasWindowRef && !window.editorWindowRef?.closed;
    
    console.log("Editor window state:", { hasWindowRef, windowIsOpen });
    
    if (windowIsOpen) {
      console.log("Found existing editor window, sending new tab message");
      
      try {
        // Send the message to add a new tab
        window.editorWindowRef?.postMessage({
          type: 'ADD_NEW_TAB',
          payload: fileData,
          timestamp: Date.now()  // Add timestamp to ensure message uniqueness
        }, window.location.origin);
        
        console.log("Message sent to editor window");
        
        // Focus the editor window
        window.editorWindowRef?.focus();
        
        toast({
          title: "File sent to editor",
          description: `Added "${fileName}" as a new tab in editor window`
        });
        
        // No longer need to extract the session ID since we're not broadcasting
        
        return;
      } catch (e) {
        console.error("Error sending message to editor window:", e);
        // Fall through to opening a new window
      }
    }
    
    // We need to open a new window
    console.log("Opening new editor window");
    
    // Create a unique session ID for localStorage
    const editorSessionId = `editor_${Date.now()}`;
    
    // Store data in localStorage
    localStorage.setItem(editorSessionId, JSON.stringify({
      tabs: [fileData]
    }));
    console.log("Stored editor data in localStorage with ID:", editorSessionId);
    
    // Open the window with specific features to force it to be a window not a tab
    // Adding token to URL for WebSocket authentication
    const newWindow = window.open(
      `/editor?session=${editorSessionId}&conversationId=${conversationId}&token=${encodeURIComponent(token || '')}&email=${encodeURIComponent(user?.email || '')}&name=${encodeURIComponent(user?.username || '')}`, 
      'editor_window',
      'width=1000,height=800,left=100,top=100,resizable=yes,scrollbars=yes,toolbar=no,menubar=no,location=no,status=yes'
    );
    
    if (!newWindow) {
      console.error("Failed to open editor window - popup might be blocked");
      toast({
        title: "Editor Error",
        description: "Failed to open editor window. Please check if popups are blocked.",
        variant: "destructive"
      });
      return;
    }
    
    // Store the reference to the new window
    window.editorWindowRef = newWindow;
    console.log("Stored reference to new editor window");
    
    // Add event listener for when window closes
    newWindow.addEventListener('beforeunload', () => {
      console.log("Editor window closing");
      window.editorWindowRef = null;
    });
    
    toast({
      title: "Opening editor",
      description: `File "${fileName}" opened in editor window`
    });
    
    // We still need the session ID for editor functionality, but we're no longer announcing it
  };

  return (
    <div className={`flex ${message.sender.is_owner ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`${getMessageClasses()} flex flex-col break-words`}>
        <div className="flex items-center gap-2 mb-1">
          {message.sender.type === 'user' && (
            <div className={`w-10 h-10 rounded-full flex items-center justify-center text-white font-bold ${getAvatarColor(message.sender.email || user?.email || '')}`}>
              {getInitial(message.sender.email || user?.email || '')}
            </div>
          )}
          <span className="font-medium text-xs">
            {message.sender.type === 'user'
              ? (message.sender.email || user?.email || 'Unknown') 
              : formatAgentName(enhancedMessage.agent_type, message.sender.email)}
          </span>
          <span className="text-xs text-gray-500 ml-auto">
            {formatDate(message.timestamp)}
          </span>
          
          {/* Show streaming indicator in header */}
          {messageIsStreaming && (
            <span className="text-xs text-blue-600 ml-1 animate-pulse">
              streaming...
            </span>
          )}
        </div>
        
        <div className={messageIsStreaming ? "streaming-content" : ""}>
          {renderContent()}
        </div>
        
        <div className="mt-2 flex items-center gap-2">
          <button 
            onClick={handleCopy}
            className="text-gray-600 hover:text-gray-900"
            aria-label="Copy content"
          >
            <Copy className="w-4 h-4" />  
          </button>
          
          {/* Only show download button for completed messages */}
          {!messageIsStreaming && (
            <DownloadButton
              content={message.content}
              defaultFileName={`${hasMessageInfo(message) && message.message_info?.file_name || `message_${formatDate(message.timestamp)}`}`}
            />
          )}
        </div>

        {responseTime && !messageIsStreaming && (
          <div className="mt-2 text-xs text-gray-500">
            Response time: {responseTime}
          </div>  
        )}
      </div>
    </div>
  );
};

// Add CSS for typing indicator and streaming content
const TypingIndicatorStyles = () => (
  <style jsx global>{`
    .typing-indicator {
      display: inline-flex;
      align-items: center;
    }

    .typing-indicator .dot {
      display: inline-block;
      width: 4px;
      height: 4px;
      border-radius: 50%;
      margin: 0 1px;
      background-color: currentColor;
      animation: typingAnimation 1.4s infinite ease-in-out;
    }

    .typing-indicator .dot:nth-child(1) {
      animation-delay: 0s;
    }

    .typing-indicator .dot:nth-child(2) {
      animation-delay: 0.2s;
    }

    .typing-indicator .dot:nth-child(3) {
      animation-delay: 0.4s;
    }

    @keyframes typingAnimation {
      0%, 60%, 100% {
        transform: translateY(0);
        opacity: 0.6;
      }
      30% {
        transform: translateY(-4px);
        opacity: 1;
      }
    }

    /* Streaming content styles */
    .streaming-content {
      white-space: pre-wrap;
      line-height: 1.5;
      overflow-wrap: break-word;
      word-wrap: break-word;
      word-break: break-all;
      max-width: 100%;
    }

    /* Hide unnecessary markers in streaming output */
    .streaming-content:not(:empty) {
      position: relative;
    }

    /* Math display styles */
    .math-display {
      margin: 1rem 0;
      padding: 0.5rem;
      background-color: #f9f9f9;
      border-radius: 4px;
      border-left: 3px solid #0066cc;
      font-family: serif;
      font-style: italic;
    }

    /* Document link styles */
    .document-link {
      color: #0066cc !important;
      text-decoration: underline !important;
      cursor: pointer !important;
      font-weight: 500 !important;
      transition: color 0.2s ease !important;
      position: relative !important;
      z-index: 10 !important;
      display: inline-block !important;
      pointer-events: auto !important;
      overflow-wrap: break-word !important;
      word-break: break-word !important;
    }

    .document-link:hover {
      color: #004499 !important;
      text-decoration: underline !important;
    }

    .document-link:focus {
      outline: 2px solid #0066cc !important;
      outline-offset: 2px !important;
    }
    
    /* Markdown content styles */
    .markdown-content h1 {
      font-size: 1.5rem;
      font-weight: 700;
      margin-top: 1.5rem;
      margin-bottom: 0.75rem;
      overflow-wrap: break-word;
      word-break: break-word;
    }
    
    .markdown-content h2 {
      font-size: 1.3rem;
      font-weight: 600;
      margin-top: 1.25rem;
      margin-bottom: 0.5rem;
      overflow-wrap: break-word;
      word-break: break-word;
    }
    
    .markdown-content h3 {
      font-size: 1.1rem;
      font-weight: 600;
      margin-top: 1rem;
      margin-bottom: 0.5rem;
      overflow-wrap: break-word;
      word-break: break-word;
    }
    
    .markdown-content h4, 
    .markdown-content h5, 
    .markdown-content h6 {
      font-size: 1rem;
      font-weight: 600;
      margin-top: 0.75rem;
      margin-bottom: 0.5rem;
      overflow-wrap: break-word;
      word-break: break-word;
    }
    
    .markdown-content code {
      font-family: monospace;
      background-color: #f0f0f0;
      padding: 0.15rem 0.3rem;
      border-radius: 3px;
      font-size: 0.9em;
      overflow-wrap: break-word;
      word-break: break-word;
      max-width: 100%;
    }
    
    .markdown-content pre {
      white-space: pre-wrap;
      max-width: 100%;
    }
    
    .markdown-content pre code {
      display: block;
      padding: 0.75rem;
      margin: 0.75rem 0;
      line-height: 1.5;
      background-color: #f5f5f5;
      border-radius: 5px;
      overflow-x: auto;
      word-wrap: break-word;
      word-break: break-all;
      white-space: pre-wrap;
    }
    
    .markdown-content blockquote {
      border-left: 3px solid #ccc;
      padding-left: 0.75rem;
      margin-left: 0;
      color: #555;
      margin: 0.75rem 0;
      overflow-wrap: break-word;
      word-break: break-word;
    }
    
    .markdown-content a {
      color: #0066cc;
      text-decoration: underline;
      transition: color 0.2s ease;
      overflow-wrap: break-word;
      word-break: break-word;
    }
    
    .markdown-content a:hover {
      color: #004499;
    }
    
    .markdown-content ol,
    .markdown-content ul {
      padding-left: 1.5rem;
      margin: 0.5rem 0;
      overflow-wrap: break-word;
      word-break: break-word;
    }
    
    .markdown-content li {
      margin-bottom: 0.25rem;
      overflow-wrap: break-word;
      word-break: break-word;
    }
    
    .markdown-content hr {
      margin: 1rem 0;
      border: 0;
      border-top: 1px solid #ddd;
    }
    
    .markdown-content p {
      overflow-wrap: break-word;
      word-break: break-word;
      margin-bottom: 0.75rem;
    }

    /* Document action styles - smaller buttons for actions */
    .document-action {
      display: inline-block !important;
      margin-top: 4px !important;
      margin-right: 8px !important;
      padding: 2px 8px !important;
      background-color: #f0f7ff !important;
      color: #0066cc !important;
      border-radius: 4px !important;
      font-size: 0.75rem !important;
      font-weight: 500 !important;
      text-decoration: none !important;
      transition: all 0.2s ease !important;
      position: relative !important;
      z-index: 10 !important;
      pointer-events: auto !important;
    }

    .document-action:hover {
      background-color: #e0f0ff !important;
      color: #004499 !important;
      text-decoration: none !important;
    }

    /* Document search results styling */
    .document-search-results {
      white-space: pre-wrap;
      line-height: 1.5;
      overflow-wrap: break-word;
      word-break: break-word;
      position: relative;
      pointer-events: auto;
      max-width: 100%;
    }

    .document-search-results a {
      color: #0066cc !important;
      text-decoration: underline !important;
      cursor: pointer !important;
      position: relative !important;
      z-index: 10 !important;
      display: inline-block !important;
      pointer-events: auto !important;
      overflow-wrap: break-word !important;
      word-break: break-word !important;
    }

    .document-search-results a:hover {
      color: #004499 !important;
      text-decoration: underline !important;
    }

    .document-search-results h3 {
      font-size: 1.1rem;
      font-weight: 600;
      margin-top: 1rem;
      margin-bottom: 0.5rem;
      overflow-wrap: break-word;
      word-break: break-word;
    }

    .document-search-results strong {
      font-weight: bold;
    }

    .document-search-results hr {
      margin: 1rem 0;
      border: 0;
      border-top: 1px solid #ddd;
    }
    
    .document-search-results p {
      overflow-wrap: break-word;
      word-break: break-word;
      margin-bottom: 0.75rem;
    }

    .document-search-results pre,
    .document-search-results code {
      white-space: pre-wrap;
      overflow-wrap: break-word;
      word-break: break-all;
      max-width: 100%;
    }

    .document-note {
      margin-top: 1.5rem;
      color: #666;
      font-size: 0.9rem;
    }

    .document-actions {
      display: flex;
      gap: 10px;
      margin-top: 5px;
      margin-bottom: 10px;
    }

    .extracted-text {
      margin: 8px 0;
      padding: 8px;
      background-color: #f5f5f5;
      border-left: 3px solid #0066cc;
      border-radius: 4px;
      font-size: 0.9rem;
      overflow-x: auto;
      white-space: pre-wrap;
    }

    .search-header {
      font-weight: bold;
      font-size: 1.1rem;
      margin-bottom: 10px;
      padding-bottom: 5px;
      border-bottom: 1px solid #ddd;
    }

    .document-header {
      font-weight: 600;
      margin-top: 15px;
      margin-bottom: 8px;
      padding-top: 5px;
    }

    .relevance-score {
      font-size: 0.85rem;
      color: #555;
      font-weight: 500;
      background-color: #f0f7ff;
      padding: 2px 6px;
      border-radius: 4px;
      display: inline-block;
      margin-left: 4px;
    }

    .section-label {
      font-weight: bold;
      color: #333;
    }

    .summary-section {
      margin: 5px 0;
    }

    .extract-section {
      margin-top: 8px;
    }

    .download-section {
      margin-top: 15px;
      padding-top: 10px;
      border-top: 1px dashed #ccc;
      display: flex;
      gap: 10px;
    }
  </style>
);

// Export both the component and the styles
export { TypingIndicatorStyles };
export default React.memo(MessageItem);left: 3px solid #0066cc;
      font-family: serif;
      font-style: italic;
    }

    /* Document link styles */
    .document-link {
      color: #0066cc !important;
      text-decoration: underline !important;
      cursor: pointer !important;
      font-weight: 500 !important;
      transition: color 0.2s ease !important;
      position: relative !important;
      z-index: 10 !important;
      display: inline-block !important;
      pointer-events: auto !important;
      overflow-wrap: break-word !important;
      word-break: break-word !important;
    }

    .document-link:hover {
      color: #004499 !important;
      text-decoration: underline !important;
    }

    .document-link:focus {
      outline: 2px solid #0066cc !important;
      outline-offset: 2px !important;
    }
    
    /* Markdown content styles */
    .markdown-content h1 {
      font-size: 1.5rem;
      font-weight: 700;
      margin-top: 1.5rem;
      margin-bottom: 0.75rem;
      overflow-wrap: break-word;
      word-break: break-word;
    }
    
    .markdown-content h2 {
      font-size: 1.3rem;
      font-weight: 600;
      margin-top: 1.25rem;
      margin-bottom: 0.5rem;
      overflow-wrap: break-word;
      word-break: break-word;
    }
    
    .markdown-content h3 {
      font-size: 1.1rem;
      font-weight: 600;
      margin-top: 1rem;
      margin-bottom: 0.5rem;
      overflow-wrap: break-word;
      word-break: break-word;
    }
    
    .markdown-content h4, 
    .markdown-content h5, 
    .markdown-content h6 {
      font-size: 1rem;
      font-weight: 600;
      margin-top: 0.75rem;
      margin-bottom: 0.5rem;
      overflow-wrap: break-word;
      word-break: break-word;
    }
    
    .markdown-content code {
      font-family: monospace;
      background-color: #f0f0f0;
      padding: 0.15rem 0.3rem;
      border-radius: 3px;
      font-size: 0.9em;
      overflow-wrap: break-word;
      word-break: break-word;
      max-width: 100%;
    }
    
    .markdown-content pre {
      white-space: pre-wrap;
      max-width: 100%;
    }
    
    .markdown-content pre code {
      display: block;
      padding: 0.75rem;
      margin: 0.75rem 0;
      line-height: 1.5;
      background-color: #f5f5f5;
      border-radius: 5px;
      overflow-x: auto;
      word-wrap: break-word;
      word-break: break-all;
      white-space: pre-wrap;
    }
    
    .markdown-content blockquote {
      border-left: 3px solid #ccc;
      padding-left: 0.75rem;
      margin-left: 0;
      color: #555;
      margin: 0.75rem 0;
      overflow-wrap: break-word;
      word-break: break-word;
    }
    
    .markdown-content a {
      color: #0066cc;
      text-decoration: underline;
      transition: color 0.2s ease;
      overflow-wrap: break-word;
      word-break: break-word;
    }
    
    .markdown-content a:hover {
      color: #004499;
    }
    
    .markdown-content ol,
    .markdown-content ul {
      padding-left: 1.5rem;
      margin: 0.5rem 0;
      overflow-wrap: break-word;
      word-break: break-word;
    }
    
    .markdown-content li {
      margin-bottom: 0.25rem;
      overflow-wrap: break-word;
      word-break: break-word;
    }
    
    .markdown-content hr {
      margin: 1rem 0;
      border: 0;
      border-top: 1px solid #ddd;
    }
    
    .markdown-content p {
      overflow-wrap: break-word;
      word-break: break-word;
      margin-bottom: 0.75rem;
    }

    /* Document action styles - smaller buttons for actions */
    .document-action {
      display: inline-block !important;
      margin-top: 4px !important;
      margin-right: 8px !important;
      padding: 2px 8px !important;
      background-color: #f0f7ff !important;
      color: #0066cc !important;
      border-radius: 4px !important;
      font-size: 0.75rem !important;
      font-weight: 500 !important;
      text-decoration: none !important;
      transition: all 0.2s ease !important;
      position: relative !important;
      z-index: 10 !important;
      pointer-events: auto !important;
    }

    .document-action:hover {
      background-color: #e0f0ff !important;
      color: #004499 !important;
      text-decoration: none !important;
    }

    /* Document search results styling */
    .document-search-results {
      white-space: pre-wrap;
      line-height: 1.5;
      overflow-wrap: break-word;
      word-break: break-word;
      position: relative;
      pointer-events: auto;
      max-width: 100%;
    }

    .document-search-results a {
      color: #0066cc !important;
      text-decoration: underline !important;
      cursor: pointer !important;
      position: relative !important;
      z-index: 10 !important;
      display: inline-block !important;
      pointer-events: auto !important;
      overflow-wrap: break-word !important;
      word-break: break-word !important;
    }

    .document-search-results a:hover {
      color: #004499 !important;
      text-decoration: underline !important;
    }

    .document-search-results h3 {
      font-size: 1.1rem;
      font-weight: 600;
      margin-top: 1rem;
      margin-bottom: 0.5rem;
      overflow-wrap: break-word;
      word-break: break-word;
    }

    .document-search-results strong {
      font-weight: bold;
    }

    .document-search-results hr {
      margin: 1rem 0;
      border: 0;
      border-top: 1px solid #ddd;
    }
    
    .document-search-results p {
      overflow-wrap: break-word;
      word-break: break-word;
      margin-bottom: 0.75rem;
    }

    .document-search-results pre,
    .document-search-results code {
      white-space: pre-wrap;
      overflow-wrap: break-word;
      word-break: break-all;
      max-width: 100%;
    }

    .document-note {
      margin-top: 1.5rem;
      color: #666;
      font-size: 0.9rem;
    }

    .document-actions {
      display: flex;
      gap: 10px;
      margin-top: 5px;
      margin-bottom: 10px;
    }

    .extracted-text {
      margin: 8px 0;
      padding: 8px;
      background-color: #f5f5f5;
      border-left: 3px solid #0066cc;
      border-radius: 4px;
      font-size: 0.9rem;
      overflow-x: auto;
      white-space: pre-wrap;
    }

    .search-header {
      font-weight: bold;
      font-size: 1.1rem;
      margin-bottom: 10px;
      padding-bottom: 5px;
      border-bottom: 1px solid #ddd;
    }

    .document-header {
      font-weight: 600;
      margin-top: 15px;
      margin-bottom: 8px;
      padding-top: 5px;
    }

    .relevance-score {
      font-size: 0.85rem;
      color: #555;
      font-weight: 500;
      background-color: #f0f7ff;
      padding: 2px 6px;
      border-radius: 4px;
      display: inline-block;
      margin-left: 4px;
    }

    .section-label {
      font-weight: bold;
      color: #333;
    }

    .summary-section {
      margin: 5px 0;
    }

    .extract-section {
      margin-top: 8px;
    }

    .download-section {
      margin-top: 15px;
      padding-top: 10px;
      border-top: 1px dashed #ccc;
      display: flex;
      gap: 10px;
    }
  </style>
);

// Export both the component and the styles
export { TypingIndicatorStyles };
export default React.memo(MessageItem); !important;
      font-weight: 500 !important;
      transition: color 0.2s ease !important;
      position: relative !important;
      z-index: 10 !important;
      display: inline-block !important;
      pointer-events: auto !important;
      overflow-wrap: break-word !important;
      word-break: break-word !important;
    }

    .document-link:hover {
      color: #004499 !important;
      text-decoration: underline !important;
    }

    .document-link:focus {
      outline: 2px solid #0066cc !important;
      outline-offset: 2px !important;
    }
    
    /* Markdown content styles */
    .markdown-content h1 {
      font-size: 1.5rem;
      font-weight: 700;
      margin-top: 1.5rem;
      margin-bottom: 0.75rem;
      overflow-wrap: break-word;
      word-break: break-word;
    }
    
    .markdown-content h2 {
      font-size: 1.3rem;
      font-weight: 600;
      margin-top: 1.25rem;
      margin-bottom: 0.5rem;
      overflow-wrap: break-word;
      word-break: break-word;
    }
    
    .markdown-content h3 {
      font-size: 1.1rem;
      font-weight: 600;
      margin-top: 1rem;
      margin-bottom: 0.5rem;
      overflow-wrap: break-word;
      word-break: break-word;
    }
    
    .markdown-content h4, 
    .markdown-content h5, 
    .markdown-content h6 {
      font-size: 1rem;
      font-weight: 600;
      margin-top: 0.75rem;
      margin-bottom: 0.5rem;
      overflow-wrap: break-word;
      word-break: break-word;
    }
    
    .markdown-content code {
      font-family: monospace;
      background-color: #f0f0f0;
      padding: 0.15rem 0.3rem;
      border-radius: 3px;
      font-size: 0.9em;
      overflow-wrap: break-word;
      word-break: break-word;
      max-width: 100%;
    }
    
    .markdown-content pre {
      white-space: pre-wrap;
      max-width: 100%;
    }
    
    .markdown-content pre code {
      display: block;
      padding: 0.75rem;
      margin: 0.75rem 0;
      line-height: 1.5;
      background-color: #f5f5f5;
      border-radius: 5px;
      overflow-x: auto;
      word-wrap: break-word;
      word-break: break-all;
      white-space: pre-wrap;
    }
    
    .markdown-content blockquote {
      border-left: 3px solid #ccc;
      padding-left: 0.75rem;
      margin-left: 0;
      color: #555;
      margin: 0.75rem 0;
      overflow-wrap: break-word;
      word-break: break-word;
    }
    
    .markdown-content a {
      color: #0066cc;
      text-decoration: underline;
      transition: color 0.2s ease;
      overflow-wrap: break-word;
      word-break: break-word;
    }
    
    .markdown-content a:hover {
      color: #004499;
    }
    
    .markdown-content ol,
    .markdown-content ul {
      padding-left: 1.5rem;
      margin: 0.5rem 0;
      overflow-wrap: break-word;
      word-break: break-word;
    }
    
    .markdown-content li {
      margin-bottom: 0.25rem;
      overflow-wrap: break-word;
      word-break: break-word;
    }
    
    .markdown-content hr {
      margin: 1rem 0;
      border: 0;
      border-top: 1px solid #ddd;
    }
    
    .markdown-content p {
      overflow-wrap: break-word;
      word-break: break-word;
      margin-bottom: 0.75rem;
    }

    /* Document action styles - smaller buttons for actions */
    .document-action {
      display: inline-block !important;
      margin-top: 4px !important;
      margin-right: 8px !important;
      padding: 2px 8px !important;
      background-color: #f0f7ff !important;
      color: #0066cc !important;
      border-radius: 4px !important;
      font-size: 0.75rem !important;
      font-weight: 500 !important;
      text-decoration: none !important;
      transition: all 0.2s ease !important;
      position: relative !important;
      z-index: 10 !important;
      pointer-events: auto !important;
    }

    .document-action:hover {
      background-color: #e0f0ff !important;
      color: #004499 !important;
      text-decoration: none !important;
    }

    /* Document search results styling */
    .document-search-results {
      white-space: pre-wrap;
      line-height: 1.5;
      overflow-wrap: break-word;
      word-break: break-word;
      position: relative;
      pointer-events: auto;
      max-width: 100%;
    }

    .document-search-results a {
      color: #0066cc !important;
      text-decoration: underline !important;
      cursor: pointer !important;
      position: relative !important;
      z-index: 10 !important;
      display: inline-block !important;
      pointer-events: auto !important;
      overflow-wrap: break-word !important;
      word-break: break-word !important;
    }

    .document-search-results a:hover {
      color: #004499 !important;
      text-decoration: underline !important;
    }

    .document-search-results h3 {
      font-size: 1.1rem;
      font-weight: 600;
      margin-top: 1rem;
      margin-bottom: 0.5rem;
      overflow-wrap: break-word;
      word-break: break-word;
    }

    .document-search-results strong {
      font-weight: bold;
    }

    .document-search-results hr {
      margin: 1rem 0;
      border: 0;
      border-top: 1px solid #ddd;
    }
    
    .document-search-results p {
      overflow-wrap: break-word;
      word-break: break-word;
      margin-bottom: 0.75rem;
    }

    .document-search-results pre,
    .document-search-results code {
      white-space: pre-wrap;
      overflow-wrap: break-word;
      word-break: break-all;
      max-width: 100%;
    }

    .document-note {
      margin-top: 1.5rem;
      color: #666;
      font-size: 0.9rem;
    }

    .document-actions {
      display: flex;
      gap: 10px;
      margin-top: 5px;
      margin-bottom: 10px;
    }

    .extracted-text {
      margin: 8px 0;
      padding: 8px;
      background-color: #f5f5f5;
      border-left: 3px solid #0066cc;
      border-radius: 4px;
      font-size: 0.9rem;
      overflow-x: auto;
      white-space: pre-wrap;
    }

    .search-header {
      font-weight: bold;
      font-size: 1.1rem;
      margin-bottom: 10px;
      padding-bottom: 5px;
      border-bottom: 1px solid #ddd;
    }

    .document-header {
      font-weight: 600;
      margin-top: 15px;
      margin-bottom: 8px;
      padding-top: 5px;
    }

    .relevance-score {
      font-size: 0.85rem;
      color: #555;
      font-weight: 500;
      background-color: #f0f7ff;
      padding: 2px 6px;
      border-radius: 4px;
      display: inline-block;
      margin-left: 4px;
    }

    .section-label {
      font-weight: bold;
      color: #333;
    }

    .summary-section {
      margin: 5px 0;
    }

    .extract-section {
      margin-top: 8px;
    }

    .download-section {
      margin-top: 15px;
      padding-top: 10px;
      border-top: 1px dashed #ccc;
      display: flex;
      gap: 10px;
    }
  </style>
);

// Export both the component and the styles
export { TypingIndicatorStyles };
export default React.memo(MessageItem);line !important;
      cursor: pointer !important;
      font-weight: 500 !important;
      transition: color 0.2s ease !important;
      position: relative !important;
      z-index: 10 !important;
      display: inline-block !important;
      pointer-events: auto !important;
    }

    .document-link:hover {
      color: #004499 !important;
      text-decoration: underline !important;
    }

    .document-link:focus {
      outline: 2px solid #0066cc !important;
      outline-offset: 2px !important;
    }
    
    /* Markdown content styles */
    .markdown-content h1 {
      font-size: 1.5rem;
      font-weight: 700;
      margin-top: 1.5rem;
      margin-bottom: 0.75rem;
      overflow-wrap: break-word;
      word-break: break-word;
    }
    
    .markdown-content h2 {
      font-size: 1.3rem;
      font-weight: 600;
      margin-top: 1.25rem;
      margin-bottom: 0.5rem;
      overflow-wrap: break-word;
      word-break: break-word;
    }
    
    .markdown-content h3 {
      font-size: 1.1rem;
      font-weight: 600;
      margin-top: 1rem;
      margin-bottom: 0.5rem;
      overflow-wrap: break-word;
      word-break: break-word;
    }
    
    .markdown-content h4, 
    .markdown-content h5, 
    .markdown-content h6 {
      font-size: 1rem;
      font-weight: 600;
      margin-top: 0.75rem;
      margin-bottom: 0.5rem;
      overflow-wrap: break-word;
      word-break: break-word;
    }
    
    .markdown-content code {
      font-family: monospace;
      background-color: #f0f0f0;
      padding: 0.15rem 0.3rem;
      border-radius: 3px;
      font-size: 0.9em;
      overflow-wrap: break-word;
      word-break: break-word;
      max-width: 100%;
    }
    
    .markdown-content pre {
      white-space: pre-wrap;
      max-width: 100%;
    }
    
    .markdown-content pre code {
      display: block;
      padding: 0.75rem;
      margin: 0.75rem 0;
      line-height: 1.5;
      background-color: #f5f5f5;
      border-radius: 5px;
      overflow-x: auto;
      word-wrap: break-word;
      word-break: break-all;
      white-space: pre-wrap;
    }
    
    .markdown-content blockquote {
      border-left: 3px solid #ccc;
      padding-left: 0.75rem;
      margin-left: 0;
      color: #555;
      margin: 0.75rem 0;
      overflow-wrap: break-word;
      word-break: break-word;
    }
    
    .markdown-content a {
      color: #0066cc;
      text-decoration: underline;
      transition: color 0.2s ease;
      overflow-wrap: break-word;
      word-break: break-word;
    }
    
    .markdown-content a:hover {
      color: #004499;
    }
    
    .markdown-content ol,
    .markdown-content ul {
      padding-left: 1.5rem;
      margin: 0.5rem 0;
      overflow-wrap: break-word;
      word-break: break-word;
    }
    
    .markdown-content li {
      margin-bottom: 0.25rem;
      overflow-wrap: break-word;
      word-break: break-word;
    }
    
    .markdown-content hr {
      margin: 1rem 0;
      border: 0;
      border-top: 1px solid #ddd;
    }
    
    .markdown-content p {
      overflow-wrap: break-word;
      word-break: break-word;
      margin-bottom: 0.75rem;
    }

    /* Document action styles - smaller buttons for actions */
    .document-action {
      display: inline-block !important;
      margin-top: 4px !important;
      margin-right: 8px !important;
      padding: 2px 8px !important;
      background-color: #f0f7ff !important;
      color: #0066cc !important;
      border-radius: 4px !important;
      font-size: 0.75rem !important;
      font-weight: 500 !important;
      text-decoration: none !important;
      transition: all 0.2s ease !important;
      position: relative !important;
      z-index: 10 !important;
      pointer-events: auto !important;
    }

    .document-action:hover {
      background-color: #e0f0ff !important;
      color: #004499 !important;
      text-decoration: none !important;
    }

    /* Document search results styling */
    .document-search-results {
      white-space: pre-wrap;
      line-height: 1.5;
      overflow-wrap: break-word;
      word-break: break-word;
      position: relative;
      pointer-events: auto;
      max-width: 100%;
    }

    .document-search-results a {
      color: #0066cc !important;
      text-decoration: underline !important;
      cursor: pointer !important;
      position: relative !important;
      z-index: 10 !important;
      display: inline-block !important;
      pointer-events: auto !important;
      overflow-wrap: break-word !important;
      word-break: break-word !important;
    }

    .document-search-results a:hover {
      color: #004499 !important;
      text-decoration: underline !important;
    }

    .document-search-results h3 {
      font-size: 1.1rem;
      font-weight: 600;
      margin-top: 1rem;
      margin-bottom: 0.5rem;
      overflow-wrap: break-word;
      word-break: break-word;
    }

    .document-search-results strong {
      font-weight: bold;
    }

    .document-search-results hr {
      margin: 1rem 0;
      border: 0;
      border-top: 1px solid #ddd;
    }
    
    .document-search-results p {
      overflow-wrap: break-word;
      word-break: break-word;
      margin-bottom: 0.75rem;
    }

    .document-search-results pre,
    .document-search-results code {
      white-space: pre-wrap;
      overflow-wrap: break-word;
      word-break: break-all;
      max-width: 100%;
    }

    .document-note {
      margin-top: 1.5rem;
      color: #666;
      font-size: 0.9rem;
    }

    .document-actions {
      display: flex;
      gap: 10px;
      margin-top: 5px;
      margin-bottom: 10px;
    }

    .extracted-text {
      margin: 8px 0;
      padding: 8px;
      background-color: #f5f5f5;
      border-left: 3px solid #0066cc;
      border-radius: 4px;
      font-size: 0.9rem;
      overflow-x: auto;
      white-space: pre-wrap;
    }

    .search-header {
      font-weight: bold;
      font-size: 1.1rem;
      margin-bottom: 10px;
      padding-bottom: 5px;
      border-bottom: 1px solid #ddd;
    }

    .document-header {
      font-weight: 600;
      margin-top: 15px;
      margin-bottom: 8px;
      padding-top: 5px;
    }

    .relevance-score {
      font-size: 0.85rem;
      color: #555;
      font-weight: 500;
      background-color: #f0f7ff;
      padding: 2px 6px;
      border-radius: 4px;
      display: inline-block;
      margin-left: 4px;
    }

    .section-label {
      font-weight: bold;
      color: #333;
    }

    .summary-section {
      margin: 5px 0;
    }

    .extract-section {
      margin-top: 8px;
    }

    .download-section {
      margin-top: 15px;
      padding-top: 10px;
      border-top: 1px dashed #ccc;
      display: flex;
      gap: 10px;
    }
  `}</style>
);

// Export both the component and the styles
export { TypingIndicatorStyles };
export default React.memo(MessageItem);
