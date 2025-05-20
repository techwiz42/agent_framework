// src/types/index.ts

// User types
export interface User {
  id: string
  username: string
  email: string
  createdAt: string
  tokens_remaining: number;
}

// Thread types
export interface Thread {
  id: string
  title: string
  description?: string
  ownerId: string
  createdAt: string
  updatedAt: string
  lastActivityAt: string
  participants: ThreadParticipant[]
  agents: ThreadAgent[]
}

export interface ThreadParticipant {
  userId: string
  username: string
  joinedAt: string
  lastReadAt?: string
  isActive: boolean
}

export interface ThreadAgent {
  id: string
  type: string
  isActive: boolean
  settings?: Record<string, Message>
}

// Message types
export interface Message {
  id: string
  threadId: string
  content: string
  createdAt: string
  sender: MessageSender
  metadata?: MessageMetadata
  replyTo?: string
  editedAt?: string
  deletedAt?: string
}

export interface MessageSender {
  type: 'user' | 'agent'
  id: string
  name: string
}

export interface MessageMetadata {
  readBy?: string[]
  reactions?: MessageReaction[]
  agentType?: string
  citations?: string[]
  confidence?: number
}

export interface MessageReaction {
  emoji: string
  users: string[]
}

// API Response types
export interface ApiResponse<T> {
  data: T
  error?: string
  message?: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
  hasMore: boolean
}

// WebSocket types
export interface WebSocketMessage {
  type: WebSocketMessageType
  payload: Message
  timestamp: string
}

export interface RegistrationResponse {
  message: string;
  email: string;
}

export enum WebSocketMessageType {
  MESSAGE = 'message',
  TYPING = 'typing',
  PRESENCE = 'presence',
  REACTION = 'reaction',
  AGENT_RESPONSE = 'agent_response'
}

// Form types
export interface ThreadFormData {
  title: string
  description?: string
  selectedAgents: string[]
  invitedUsers?: string[]
}

export interface MessageFormData {
  content: string
  replyTo?: string
  mentionedUsers?: string[]
  requestedAgents?: string[]
}

export interface RegistrationResponse {
  message: string;
  email: string;
}

export interface EmailVerificationResponse {
  message: string;
}

export interface ApiResponse<T> {
  data: T;
  error?: string;
  message?: string;
}
