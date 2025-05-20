import { api } from './api';

interface AgentDescriptions {
  [key: string]: string;
}

export const agentService = {
  async getAvailableAgents(token: string): Promise<string[]> {
    const response = await api.get<string[]>('/api/agents/available', {
      headers: { Authorization: `Bearer ${token}` }
    });
    return response.data;
  },

  async getAgentDescriptions(token: string): Promise<AgentDescriptions> {
    const response = await api.get<AgentDescriptions>('/api/agents/descriptions', {
      headers: { Authorization: `Bearer ${token}` }
    });
    return response.data;
  }
};
