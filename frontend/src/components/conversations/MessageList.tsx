import React from 'react';
import MessageItem from './MessageItem';

interface Message {
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
}

interface TypingUser {
  id: string;
  name: string;
}

interface MessageListProps {
  messages: Message[];
  currentUser: any;
  streamingContent?: string;
  typingUsers?: TypingUser[];
}

const MessageList: React.FC<MessageListProps> = ({ 
  messages, 
  currentUser, 
  streamingContent,
  typingUsers = []
}) => {
  if (messages.length === 0 && !streamingContent && typingUsers.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-gray-500">
        <p className="mb-2">No messages yet</p>
        <p className="text-sm">Start the conversation by typing a message below</p>
        <p className="text-sm mt-4">
          Tip: Use <code className="bg-gray-100 p-1 rounded">@AGENT</code> to direct your message to a specific agent
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {messages.map((message) => (
        <MessageItem
          key={message.id}
          message={message}
          isCurrentUser={
            currentUser && message.message_info?.participant_email === currentUser.email
          }
        />
      ))}
      
      {streamingContent && (
        <div className="flex">
          <div className="bg-blue-50 p-3 rounded-lg max-w-3xl">
            <div className="mb-1 font-medium text-blue-800">Agent</div>
            <div className="prose max-w-none" dangerouslySetInnerHTML={{ __html: streamingContent }} />
          </div>
        </div>
      )}
      
      {typingUsers.length > 0 && (
        <div className="text-gray-500 text-sm animate-pulse">
          {typingUsers.length === 1 ? (
            <span>{typingUsers[0].name} is typing...</span>
          ) : (
            <span>
              {typingUsers.map(user => user.name).join(', ')} are typing...
            </span>
          )}
        </div>
      )}
    </div>
  );
};

export default MessageList;