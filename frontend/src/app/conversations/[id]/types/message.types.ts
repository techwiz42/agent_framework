// types/message.types.ts

export interface Message {
  id: string;
  content: string;
  sender: {
    identifier: string;
    is_owner: boolean;
    email?: string;
    userEmail?: string;
    name?: string;
    message_metadata?: MessageMetadata;
    type: 'user' | 'agent' | 'moderator' | 'system';
  };
  message_info?: {
    is_file?: boolean;
    file_name?: string;
    file_type?: string;
    file_size?: number;
    is_private?: boolean;
    [key: string]: unknown;
  };
  timestamp: string;
  message_metadata?: MessageMetadata;
  agent_type?: string;
}

export interface MessageMetadata {
  agent_type?: string;
  is_file?: boolean;
  file_name?: string;
  filename?: string;
  file_type?: string;
  mime_type?: string;
  file_size?: number;
  is_private?: boolean;
  web_url?: string;
  modified_at?: string;
  file_metadata?: {
    name: string;
    type: string;
    size: number;
    id: string;
  };
  participant_name?: string;
  participant_email?: string;
  is_owner?: boolean;
  tokens_used?: number;
  source?: string;
  [key: string]: unknown;
}

export interface MessageHistory {
  id: string;
  content: string;
  created_at: string;
  participant_id?: string;
  agent_id?: string;
  message_metadata: MessageMetadata;
}

export interface MessageResponse {
  id: string;
  content: string;
  created_at: string;
  participant_id?: string; // Added this property
  agent_id?: string;
  message_info?: {
    is_file?: boolean;
    file_name?: string;
    file_type?: string;
    file_size?: number;
    is_private?: boolean;
    participant_name?: string;
    participant_email?: string;
    is_owner?: boolean;
    source?: string;
    [key: string]: unknown;
  };
  message_metadata?: MessageMetadata; // Changed to optional to match actual usage
}

export interface MessageListProps {
  messages: Message[];
  hasMoreMessages: boolean;
  isLoadingMore: boolean;
  onLoadMore: () => void;
}

export interface MessageItemProps {
  message: Message;
  formatDate: (date: string) => string;
}

// types/websocket.types.ts
export interface BaseWebSocketMessage {
  type: 'message' | 'typing_status' | 'user_joined' | 'user_left' | 'read';
  identifier: string;
  is_owner: boolean;
  timestamp: string;
}

export interface ChatMessage extends BaseWebSocketMessage {
  type: 'message';
  content: string;
  agent_type?: string;
  message_metadata?: MessageMetadata;
}

export interface TypingStatusMessage extends BaseWebSocketMessage {
  type: 'typing_status';
  is_typing: boolean;
}
