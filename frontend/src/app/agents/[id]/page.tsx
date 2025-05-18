'use client'
import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { Button } from '@/components/ui/button';
import { ArrowLeft, Bot, Edit, MessageSquare, Settings, Trash2 } from 'lucide-react';

interface Agent {
  id: string;
  name: string;
  description: string;
  agent_type: string;
  capabilities: string[];
  created_at: string;
  created_by?: string;
  settings?: Record<string, any>;
}

export default function AgentDetailPage({ params }: { params: { id: string } }) {
  const { id } = params;
  const router = useRouter();
  const { user, isLoading } = useAuth();
  const [agent, setAgent] = useState<Agent | null>(null);
  const [isLoadingAgent, setIsLoadingAgent] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isLoading && !user) {
      router.push('/login');
    }
  }, [isLoading, user, router]);

  useEffect(() => {
    if (user && id) {
      // Placeholder for future API integration
      // This would be replaced with an actual API call to fetch agent details
      const fetchAgentDetails = async () => {
        try {
          setIsLoadingAgent(true);
          setError(null);
          
          // Mocked data for now
          // In a real application, this would be: const response = await getAgent(id);
          const mockAgent: Agent = {
            id,
            name: id === '1' ? 'Business Advisor' : id === '2' ? 'Data Analyst' : 'Web Search Agent',
            description: id === '1' 
              ? 'Provides business strategy and management advice for decision-making and planning.'
              : id === '2' 
                ? 'Processes and interprets complex datasets to uncover patterns and insights.'
                : 'Searches the web for relevant information to answer your questions.',
            agent_type: id === '1' ? 'advisor' : id === '2' ? 'data_analyst' : 'web_search',
            capabilities: id === '1' 
              ? ['Business strategy', 'Management advice', 'Planning assistance']
              : id === '2'
                ? ['Data processing', 'Pattern recognition', 'Insight generation']
                : ['Web searching', 'Information retrieval', 'Query processing'],
            created_at: new Date().toISOString(),
            created_by: user.email,
            settings: {
              response_style: 'detailed',
              model: 'advanced',
              max_tokens: 4000
            }
          };
          
          setAgent(mockAgent);
        } catch (error) {
          console.error('Failed to fetch agent details:', error);
          setError('Failed to load agent details');
        } finally {
          setIsLoadingAgent(false);
        }
      };

      fetchAgentDetails();
    }
  }, [id, user, isLoading]);

  const handleCreateConversation = () => {
    // In a real app, we would create a conversation with this agent
    router.push('/conversations/new');
  };

  if (isLoading || isLoadingAgent) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error || !agent) {
    return (
      <div className="container mx-auto px-4 py-8 text-center">
        <div className="bg-red-50 text-red-700 p-4 rounded-md mb-4">
          {error || 'Agent not found'}
        </div>
        <button 
          onClick={() => router.push('/agents')}
          className="text-blue-600 hover:underline"
        >
          Back to agents
        </button>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <Button 
        variant="ghost" 
        className="mb-6 flex items-center gap-1"
        onClick={() => router.push('/agents')}
      >
        <ArrowLeft size={16} />
        Back to agents
      </Button>

      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 mb-8">
        <div className="flex flex-col md:flex-row justify-between items-start gap-4 mb-6">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center">
              <Bot className="w-8 h-8 text-blue-600" />
            </div>
            <div>
              <h1 className="text-2xl font-bold">{agent.name}</h1>
              <p className="text-gray-500">{agent.agent_type}</p>
            </div>
          </div>
          <div className="flex gap-2">
            <Button 
              variant="outline" 
              className="flex items-center gap-1"
              onClick={() => router.push(`/agents/${id}/edit`)}
            >
              <Edit size={16} />
              Edit
            </Button>
            <Button 
              variant="outline" 
              className="flex items-center gap-1 text-red-600 hover:text-red-700"
            >
              <Trash2 size={16} />
              Delete
            </Button>
            <Button 
              className="flex items-center gap-1"
              onClick={handleCreateConversation}
            >
              <MessageSquare size={16} />
              Start Conversation
            </Button>
          </div>
        </div>

        <div className="mb-8">
          <h2 className="text-lg font-semibold mb-2">Description</h2>
          <p className="text-gray-700">{agent.description}</p>
        </div>

        <div className="mb-8">
          <h2 className="text-lg font-semibold mb-2">Capabilities</h2>
          <div className="flex flex-wrap gap-2">
            {agent.capabilities.map((capability, index) => (
              <span 
                key={index} 
                className="bg-blue-50 text-blue-700 px-3 py-1 rounded-full text-sm"
              >
                {capability}
              </span>
            ))}
          </div>
        </div>

        <div>
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-lg font-semibold">Agent Settings</h2>
            <Button 
              variant="ghost" 
              size="sm"
              className="flex items-center gap-1"
              onClick={() => router.push(`/agents/${id}/settings`)}
            >
              <Settings size={14} />
              Configure
            </Button>
          </div>
          <div className="bg-gray-50 p-4 rounded-md">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {agent.settings && Object.entries(agent.settings).map(([key, value]) => (
                <div key={key} className="flex justify-between">
                  <span className="text-gray-600 capitalize">{key.replace('_', ' ')}</span>
                  <span className="font-medium">{String(value)}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
        <h2 className="text-lg font-semibold mb-4">Agent Usage</h2>
        <div className="flex justify-center items-center py-8 text-gray-500">
          <p>Usage statistics will be shown here once this agent has been used in conversations.</p>
        </div>
      </div>
    </div>
  );
}