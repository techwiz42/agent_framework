'use client'
import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { Button } from '@/components/ui/button';
import { ArrowLeft } from 'lucide-react';

interface AgentType {
  id: string;
  name: string;
  description: string;
  icon: string;
}

export default function NewAgentPage() {
  const router = useRouter();
  const { user, isLoading } = useAuth();
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [selectedType, setSelectedType] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Predefined agent types
  const agentTypes: AgentType[] = [
    {
      id: 'advisor',
      name: 'Business Advisor',
      description: 'Strategic business advice and planning assistant.',
      icon: '💼'
    },
    {
      id: 'data_analyst',
      name: 'Data Analyst',
      description: 'Process data and generate insights from datasets.',
      icon: '📊'
    },
    {
      id: 'web_search',
      name: 'Web Search',
      description: 'Search the web for information and resources.',
      icon: '🔍'
    },
    {
      id: 'document',
      name: 'Document Agent',
      description: 'Process and analyze documents and text content.',
      icon: '📄'
    },
    {
      id: 'custom',
      name: 'Custom Agent',
      description: 'Build a fully customized agent with specific capabilities.',
      icon: '⚙️'
    }
  ];

  useEffect(() => {
    if (!isLoading && !user) {
      router.push('/login');
    }
  }, [isLoading, user, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!name || !description || !selectedType) {
      return;
    }
    
    try {
      setIsSubmitting(true);
      
      // Placeholder for API call
      // In a real app, we would call an API to create the agent
      console.log('Creating agent:', {
        name,
        description,
        agent_type: selectedType
      });
      
      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Redirect to agents list
      router.push('/agents');
    } catch (error) {
      console.error('Failed to create agent:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
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

      <div className="max-w-3xl mx-auto">
        <h1 className="text-2xl font-bold mb-8">Create a New Agent</h1>

        <form onSubmit={handleSubmit}>
          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 mb-6">
            <h2 className="text-lg font-semibold mb-4">Agent Information</h2>
            
            <div className="mb-4">
              <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
                Agent Name
              </label>
              <input
                type="text"
                id="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="e.g., My Business Advisor"
                required
              />
            </div>
            
            <div className="mb-4">
              <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
                Description
              </label>
              <textarea
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Describe what this agent will do..."
                rows={3}
                required
              />
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 mb-8">
            <h2 className="text-lg font-semibold mb-4">Select Agent Type</h2>
            <div className="grid md:grid-cols-2 gap-4">
              {agentTypes.map((type) => (
                <div
                  key={type.id}
                  className={`border rounded-lg p-4 cursor-pointer hover:bg-gray-50 transition-colors
                    ${selectedType === type.id ? 'border-blue-500 bg-blue-50' : 'border-gray-200'}`}
                  onClick={() => setSelectedType(type.id)}
                >
                  <div className="flex items-center gap-3">
                    <div className="text-2xl">{type.icon}</div>
                    <div>
                      <h3 className="font-medium">{type.name}</h3>
                      <p className="text-sm text-gray-500">{type.description}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="flex justify-end">
            <Button
              type="button"
              variant="outline"
              className="mr-2"
              onClick={() => router.push('/agents')}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={!name || !description || !selectedType || isSubmitting}
            >
              {isSubmitting ? 'Creating...' : 'Create Agent'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}