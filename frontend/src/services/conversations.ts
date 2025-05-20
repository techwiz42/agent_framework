import { api, getAuthHeaders } from './api'
import { Conversation, ThreadFormData } from '@/types/conversation'
import { MessageResponse } from '@/app/conversations/[id]/types/message.types';

interface ConversationListResponse {
  items: Conversation[];
  total: number;
  page: number;
  size: number;
}

interface ConversationCreateRequest {
  title: string;
  description: string | null;
  agent_types: string[];
  participants: Array<{
    email: string;
    name: string | null;
  }>;
}

interface InviteRequest {
  usernames: string[];
}

interface ParticipantResponse {
  message: string;
}

export const conversationService = {
  async getConversations(token: string) {
    try {
      const response = await api.get<ConversationListResponse>(
        '/api/conversations/',
        { headers: getAuthHeaders(token) }
      );
      console.log('Conversation service raw response:', response);
      console.log('Conversation service data:', response.data);
      return response;
    } catch (error) {
      console.error('Error in getConversations:', error);
      throw error;
    }
  },

  async getConversation(conversationId: string, token: string) {
    try {
      const response = await api.get<Conversation>(
        `/api/conversations/${conversationId}`,
        { headers: getAuthHeaders(token) }
      );
      return response;
    } catch (error) {
      console.error(`Error fetching conversation ${conversationId}:`, error);
      throw error;
    }
  },

  async getMessages(conversationId: string, token: string) {
    try {
      const response = await api.get<MessageResponse[]>(
        `/api/conversations/${conversationId}/messages`,
        { headers: getAuthHeaders(token) }
      );
      return response;
    } catch (error) {
      console.error('Error fetching messages:', error);
      throw error;
    }
  },

  async createConversation(data: ThreadFormData, token: string) {
    try {
      const requestData: ConversationCreateRequest = {
        title: data.title,
        description: data.description || null,
        agent_types: data.selectedAgents,
        participants: data.participantEmails.map(email => ({
          email,
          name: null
        }))
      };

      console.log('Creating conversation with data:', requestData);

      const response = await api.post<Conversation>(
        '/api/conversations/',
        requestData,
        {
          headers: {
            ...getAuthHeaders(token),
            'Content-Type': 'application/json'
          }
        }
      );
      return response;
    } catch (error) {
      console.error('Error creating conversation:', error);
      throw error;
    }
  },

  async inviteToConversation(conversationId: string, usernames: string[], token: string) {
    try {
      const requestData: InviteRequest = { usernames };
      const response = await api.post(
        `/api/conversations/${conversationId}/invite`,
        requestData,
        { 
          headers: {
            ...getAuthHeaders(token),
            'Content-Type': 'application/json'
          }
        }
      );
      return response;
    } catch (error) {
      console.error(`Error inviting users to conversation ${conversationId}:`, error);
      throw error;
    }
  },

  async updateConversation(conversationId: string, data: Partial<ThreadFormData>, token: string) {
    try {
      const response = await api.patch<Conversation>(
        `/api/conversations/${conversationId}`,
        data,
        {
          headers: {
            ...getAuthHeaders(token),
            'Content-Type': 'application/json'
          }
        }
      );
      return response;
    } catch (error) {
      console.error(`Error updating conversation ${conversationId}:`, error);
      throw error;
    }
  },
  
  async sendInvitations(conversationId: string, token: string) {
    try {
      const response = await api.post(
        `/api/conversations/${conversationId}/send-invitations`,
        {},  // empty body since participants are already stored
        {
          headers: getAuthHeaders(token)
        }
      );
      return response;
    } catch (error) {
      console.error('Error sending conversation invitations:', error);
      throw error;
    }
  },

  async deleteConversation(conversationId: string, token: string) {
   try {
      const response = await api.delete(`/api/conversations/${conversationId}`, {
        headers: {
          ...getAuthHeaders(token),
          'Content-Type': 'application/json'
        }
      });

      if ('status' in response && typeof response.status === 'number') {
        // Return true if status code is 2xx
        console.log("Response status:", response.status)
        return [200, 204].includes(response.status); 
      }
      else {
       console.error("Response object does not have a valid status property.");
       return false;
     }	     
   } catch (error) {
      console.error(`Error deleting conversation ${conversationId}:`, error);
      throw error;
    }
  },

  async addParticipant(
    conversationId: string, 
    participantData: { email: string }, 
    token: string
  ): Promise<ParticipantResponse> {
    const response = await api.post(
      `/api/conversations/${conversationId}/add-participant`, 
      participantData, 
      {
        headers: { 
          'Authorization': `Bearer ${token}` 
        }
      }
    );

    // Type guard to check if response.data has a message property
    const hasMessage = (data: unknown): data is ParticipantResponse => {
      return typeof data === 'object' && data !== null && typeof (data as Record<string, unknown>).message === 'string';
    };

    if (hasMessage(response.data)) {
      return response.data;
    }

    // Return default message if response doesn't include one
    return { message: 'Participant added successfully' };
  },

  async removeParticipant(
    conversationId: string, 
    email: string,
    token: string
  ): Promise<void> {
    // For DELETE requests with body, we need to use a different approach
    // since the fetch API doesn't directly support bodies in DELETE requests
    const url = `/api/conversations/${conversationId}/remove-participant?email=${encodeURIComponent(email)}`;
    await api.delete(url, {
      headers: { 
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
  }
};
