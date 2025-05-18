'use client'
import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { Button } from '@/components/ui/button';
import { Bot, Plus } from 'lucide-react';

interface Agent {
  id: string;
  name: string;
  description: string;
  agent_type: string;
  capabilities: string[];
  created_at: string;
}

export default function AgentsPage() {
  const router = useRouter();
  const { user, isLoading } = useAuth();
  const [agents, setAgents] = useState<Agent[]>([]);
  const [isLoadingAgents, setIsLoadingAgents] = useState(true);

  useEffect(() => {
    if (!isLoading && !user) {
      router.push('/login');
    }
  }, [isLoading, user, router]);

  useEffect(() => {
    if (user) {
      // Placeholder for future API integration
      // This would be replaced with an actual API call to fetch agents
      const fetchAgents = async () => {
        try {
          setIsLoadingAgents(true);
          // Mocked data for now
          const mockAgents: Agent[] = [
            {
              id: '1',
              name: 'Business Advisor',
              description: 'Provides business strategy and management advice for decision-making and planning.',
              agent_type: 'advisor',
              capabilities: ['Business strategy', 'Management advice', 'Planning assistance'],
              created_at: new Date().toISOString()
            },
            {
              id: '2',
              name: 'Data Analyst',
              description: 'Processes and interprets complex datasets to uncover patterns and insights.',
              agent_type: 'data_analyst',
              capabilities: ['Data processing', 'Pattern recognition', 'Insight generation'],
              created_at: new Date().toISOString()
            },
            {
              id: '3',
              name: 'Web Search Agent',
              description: 'Searches the web for relevant information to answer your questions.',
              agent_type: 'web_search',
              capabilities: ['Web searching', 'Information retrieval', 'Query processing'],
              created_at: new Date().toISOString()
            }
          ];
          
          setAgents(mockAgents);
        } catch (error) {
          console.error('Failed to fetch agents:', error);
        } finally {
          setIsLoadingAgents(false);
        }
      };

      fetchAgents();
    }
  }, [user]);

  if (isLoading || isLoadingAgents) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-2xl font-bold">AI Agents</h1>
        <Button
          onClick={() => router.push('/agents/new')}
          className="flex items-center gap-2"
        >
          <Plus size={16} />
          Create Custom Agent
        </Button>
      </div>

      {agents.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg border border-gray-200">
          <Bot className="mx-auto h-12 w-12 text-gray-400 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No agents configured</h3>
          <p className="text-gray-500 mb-6">Create a custom agent or use our built-in agents</p>
          <Button
            onClick={() => router.push('/agents/new')}
            className="flex items-center gap-2 mx-auto"
          >
            <Plus size={16} />
            Create Agent
          </Button>
        </div>
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {agents.map((agent) => (
            <div key={agent.id} className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
              <div className="flex justify-between items-start mb-4">
                <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                  <Bot className="w-6 h-6 text-blue-600" />
                </div>
                <Button variant="ghost" size="sm" onClick={() => router.push(`/agents/${agent.id}`)}>
                  Details
                </Button>
              </div>
              <h3 className="text-xl font-semibold mb-2">{agent.name}</h3>
              <p className="text-gray-600 mb-4">{agent.description}</p>
              <div className="mt-4">
                <h4 className="text-sm font-medium text-gray-500 mb-2">Capabilities:</h4>
                <div className="flex flex-wrap gap-2">
                  {agent.capabilities.map((capability, index) => (
                    <span key={index} className="bg-blue-50 text-blue-700 text-xs px-2 py-1 rounded-full">
                      {capability}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}