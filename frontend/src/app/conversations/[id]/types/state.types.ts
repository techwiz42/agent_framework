import { ThreadAgent } from '@/types/conversation';

export interface SystemState {
  moderatorAnalyzing: boolean;
  activeAgent: ThreadAgent | null;
  agentTyping: boolean;
}

export interface LoadingState {
  isLoading: boolean;
  isLoadingMore: boolean;
  hasMoreMessages: boolean;
}

export interface TypingIndicatorProps {
  typingUsers: Set<string>;
  getParticipantName: (id: string) => string;
}

export interface MessageInputProps {
  onSendMessage: (message: string) => void;
  disabled?: boolean;
}

export interface TypingState {
  [agentId: string]: {
    isTyping: boolean;
    agentType: string;
  };
}
