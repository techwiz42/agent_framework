export interface ThreadParticipant {
  id: string;
  email: string;
  name?: string;
  joined_at: string;
  last_read_at?: string;
  is_active: boolean;
}

export interface ThreadAgent {
  id: string;
  thread_id: string;
  agent_type: string;
  is_active: boolean;
  settings: Record<string, unknown>;
  created_at: string;
}

export interface Thread {
  id: string;
  title: string;
  description?: string;
  owner_id: string;
  status: 'active' | 'archived' | 'closed';
  settings: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  participants: ThreadParticipant[];
  agents: ThreadAgent[];
}

export interface ThreadFormData {
  title: string;
  description?: string;
  selectedAgents: string[];
  participantEmails: string[];
}

export interface ThreadListResponse {
  items: Thread[];
  total: number;
  page: number;
  size: number;
}

export interface ParticipantCreate {
  email: string;
  name: string | null;
}

export interface ThreadCreate {
  title: string;
  description?: string | null;
  participants: ParticipantCreate[];
  agent_types: string[];
  settings?: Record<string, unknown>;
}

// API Response type
export interface ApiResponse<T> {
  status: number;
  data: T;
}

// Type aliases for consistency
export type Conversation = Thread;
export type ConversationListResponse = ThreadListResponse;
