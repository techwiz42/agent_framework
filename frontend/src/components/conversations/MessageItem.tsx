import React from 'react';
import { formatDistanceToNow } from 'date-fns';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { atomDark } from 'react-syntax-highlighter/dist/cjs/styles/prism';

interface MessageProps {
  message: {
    id: string;
    content: string;
    created_at: string;
    participant_id?: string;
    agent_id?: string;
    message_info?: {
      participant_name?: string;
      participant_email?: string;
      is_owner?: boolean;
      source?: string;
      file_name?: string;
      file_type?: string;
      programming_language?: string;
    };
  };
  isCurrentUser: boolean;
}

const MessageItem: React.FC<MessageProps> = ({ message, isCurrentUser }) => {
  const isAgent = message.agent_id || message.message_info?.source?.toUpperCase() !== 'USER';
  const displayName = message.message_info?.participant_name || 
                     (isAgent ? message.message_info?.source : 'Unknown User');
  
  const formattedTime = message.created_at ? 
    formatDistanceToNow(new Date(message.created_at), { addSuffix: true }) : '';
  
  // Check if message contains a file display component
  const hasFileDisplay = message.content.includes('<script type="application/vnd.ant.editable">');

  // Process the content to extract file information
  const processFileDisplay = (content: string) => {
    try {
      const scriptMatch = content.match(/<script type="application\/vnd\.ant\.editable">(.*?)<\/script>/s);
      if (scriptMatch && scriptMatch[1]) {
        const fileData = JSON.parse(scriptMatch[1]);
        return (
          <div className="mt-2 border rounded-md overflow-hidden">
            <div className="bg-gray-100 px-3 py-2 border-b flex justify-between items-center">
              <span className="font-mono text-sm">{fileData.fileName}</span>
            </div>
            <SyntaxHighlighter
              language={fileData.fileType || 'text'}
              style={atomDark}
              showLineNumbers
              customStyle={{ margin: 0, borderRadius: 0 }}
            >
              {fileData.content}
            </SyntaxHighlighter>
          </div>
        );
      }
    } catch (e) {
      console.error('Error processing file display:', e);
    }
    return null;
  };

  // Process content for markdown and code blocks
  const renderContent = () => {
    if (hasFileDisplay) {
      const textPart = message.content.replace(/<script type="application\/vnd\.ant\.editable">.*?<\/script>/s, '');
      return (
        <>
          {textPart && (
            <ReactMarkdown
              components={{
                code({ node, inline, className, children, ...props }) {
                  const match = /language-(\w+)/.exec(className || '');
                  return !inline && match ? (
                    <SyntaxHighlighter
                      language={match[1]}
                      style={atomDark}
                      PreTag="div"
                      {...props}
                    >
                      {String(children).replace(/\n$/, '')}
                    </SyntaxHighlighter>
                  ) : (
                    <code className={className} {...props}>
                      {children}
                    </code>
                  );
                }
              }}
            >
              {textPart}
            </ReactMarkdown>
          )}
          {processFileDisplay(message.content)}
        </>
      );
    } else {
      return (
        <ReactMarkdown
          components={{
            code({ node, inline, className, children, ...props }) {
              const match = /language-(\w+)/.exec(className || '');
              return !inline && match ? (
                <SyntaxHighlighter
                  language={match[1]}
                  style={atomDark}
                  PreTag="div"
                  {...props}
                >
                  {String(children).replace(/\n$/, '')}
                </SyntaxHighlighter>
              ) : (
                <code className={className} {...props}>
                  {children}
                </code>
              );
            }
          }}
        >
          {message.content}
        </ReactMarkdown>
      );
    }
  };

  const messageClass = isCurrentUser
    ? 'bg-blue-100 ml-auto'
    : isAgent
      ? 'bg-blue-50'
      : 'bg-gray-100';

  return (
    <div className={`flex ${isCurrentUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`p-3 rounded-lg max-w-3xl ${messageClass}`}>
        <div className="flex justify-between items-center mb-1">
          <div className={`font-medium ${isAgent ? 'text-blue-800' : ''}`}>
            {displayName}
          </div>
          <div className="text-xs text-gray-500 ml-2">{formattedTime}</div>
        </div>
        <div className="prose max-w-none">
          {renderContent()}
        </div>
      </div>
    </div>
  );
};

export default MessageItem;