import { 
  Message,
  MessageHistory 
} from '../types/message.types';
import { formatAgentName } from './format.utils';

export const transformMessageHistory = (
  messageHistory: MessageHistory,
  userId: string | undefined,
  getParticipantName: (id: string) => string
): Message => ({
  id: messageHistory.id,
  content: messageHistory.content,
  timestamp: messageHistory.created_at,
  sender: {
    identifier: messageHistory.participant_id || messageHistory.agent_id || 'unknown',
    is_owner: messageHistory.participant_id === userId,
    name: messageHistory.participant_id 
      ? getParticipantName(messageHistory.participant_id)
      : messageHistory.agent_id 
        ? formatAgentName(messageHistory.message_metadata.agent_type as string)
        : 'Unknown',
    type: messageHistory.participant_id 
      ? 'user' 
      : messageHistory.message_metadata.agent_type === 'MODERATOR'
        ? 'moderator'
        : 'agent'
  }
});

export const createSystemMessage = (
  content: string,
  agent_type: string = 'MODERATOR'
): Message => ({
  id: crypto.randomUUID(),
  content,
  timestamp: new Date().toISOString(),
  sender: {
    identifier: agent_type,
    is_owner: false,
    name: formatAgentName(agent_type),
    type: agent_type === 'MODERATOR' ? 'moderator' : 'agent'
  }
});
