// src/types/websocket.types.ts

// Define metadata interfaces
export interface FileMetadata {
    name: string;
    type: string;
    size: number;
    id: string;
}

export interface MessageMetadata {
    file_metadata?: FileMetadata;
    participant_name?: string;
    participant_email?: string;
    is_owner?: boolean;
    tokens_used?: number;
    source?: string;
    is_file?: boolean;
    file_name?: string;
    file_type?: string;
    file_size?: number;
    is_private?: boolean;
    [key: string]: unknown; // Changed from 'any' to 'unknown'
}

export type WebSocketMessageType = 
    | 'message' 
    | 'typing_status' 
    | 'user_joined' 
    | 'user_left' 
    | 'read'
    | 'editor_open'
    | 'editor_change'
    | 'editor_close'
    | 'editor_cursor'
    | 'token';

export interface BaseWebSocketMessage {
    type: WebSocketMessageType;
    identifier: string;
    timestamp: string;
    is_owner?: boolean;
    agent_type?: string;
    message_metadata?: MessageMetadata;
}

export interface ChatMessage extends BaseWebSocketMessage {
    type: 'message';
    id?: string;
    content: string;
    sender_email?: string;
    agent_type?: string;
    name?: string;
    email?: string;
    message_metadata?: MessageMetadata;
}

export interface UserJoinedMessage extends BaseWebSocketMessage {
    type: 'user_joined';
    name?: string;
    email?: string;
}

export interface UserLeftMessage extends BaseWebSocketMessage {
    type: 'user_left';
    name?: string;
    email?: string;
}

export interface ReadMessage extends BaseWebSocketMessage {
    type: 'read';
    message_id: string;
}

export interface TypingStatusMessage extends BaseWebSocketMessage {
    type: 'typing_status';
    is_typing: boolean;
    name?: string;
    email?: string;
    participant_name?: string;
}

export interface EditorSender {
    email: string;
    name?: string;
}

export interface EditorOpenEvent extends BaseWebSocketMessage {
    type: 'editor_open';
    content: string;
    fileName: string;
    fileType: string;
    sender: EditorSender;
}

export interface EditorChangeEvent extends BaseWebSocketMessage {
    type: 'editor_change';
    content: string;
    fileName: string;
    sender: EditorSender;
}

export interface EditorCloseEvent extends BaseWebSocketMessage {
    type: 'editor_close';
    fileName: string;
    sender: EditorSender;
}

export interface EditorCursorEvent extends BaseWebSocketMessage {
    type: 'editor_cursor';
    fileName: string;
    position: {
        line: number;
        column: number;
    };
    sender: EditorSender;
}

export interface TokenMessage extends BaseWebSocketMessage {
    type: 'token';
    token: string;
    conversation_id?: string;
    agent_type?: string;
    message_id?: string;
}

// Combined WebSocketMessage type
export type WebSocketMessage = 
    | ChatMessage 
    | TypingStatusMessage 
    | UserJoinedMessage 
    | UserLeftMessage 
    | ReadMessage
    | EditorOpenEvent
    | EditorChangeEvent
    | EditorCloseEvent
    | EditorCursorEvent
    | TokenMessage;

// WebSocket configuration interface
export interface WebSocketConfig {
    conversationId: string;
    token?: string | null;
    userId?: string;
    userEmail?: string;
    onMessage: (message: ChatMessage) => void;
    onTypingStatus: (status: TypingStatusMessage) => void;
    onError?: (error: unknown) => void;
    onConnectionChange?: (connected: boolean) => void;
}
