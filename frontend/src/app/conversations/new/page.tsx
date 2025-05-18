'use client'
import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { Button } from '@/components/ui/button';
import { X, Plus, ArrowLeft } from 'lucide-react';
import { createConversation } from '@/services/api';

interface ParticipantInput {
  email: string;
  name?: string;
}

export default function NewConversationPage() {
  const router = useRouter();
  const { user, isLoading } = useAuth();
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [participants, setParticipants] = useState<ParticipantInput[]>([]);
  const [newParticipantEmail, setNewParticipantEmail] = useState('');
  const [newParticipantName, setNewParticipantName] = useState('');
  const [selectedAgents, setSelectedAgents] = useState<string[]>(['BUSINESS', 'DATASEARCH']);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  // List of available agents
  const availableAgents = [
    { type: 'BUSINESS', label: 'Business Advisor', description: 'General business strategy and management advice' },
    { type: 'BUSINESSINTELLIGENCE', label: 'Business Intelligence', description: 'Analytics and business metrics insights' },
    { type: 'DATAANALYSIS', label: 'Data Analysis', description: 'Process and interpret complex datasets' },
    { type: 'WEBSEARCH', label: 'Web Search', description: 'Search the web for information' },
    { type: 'DOCUMENTSEARCH', label: 'Document Search', description: 'Search through uploaded documents' }
  ];

  useEffect(() => {
    if (!isLoading && !user) {
      router.push('/login');
    }
  }, [isLoading, user, router]);

  const addParticipant = () => {
    if (!newParticipantEmail.trim()) return;
    
    // Simple email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(newParticipantEmail)) {
      setError('Please enter a valid email address');
      return;
    }
    
    // Check if email already exists
    if (participants.some(p => p.email.toLowerCase() === newParticipantEmail.toLowerCase())) {
      setError('This participant has already been added');
      return;
    }
    
    setParticipants([...participants, { 
      email: newParticipantEmail, 
      name: newParticipantName.trim() || undefined 
    }]);
    setNewParticipantEmail('');
    setNewParticipantName('');
    setError('');
  };

  const removeParticipant = (email: string) => {
    setParticipants(participants.filter(p => p.email !== email));
  };

  const toggleAgent = (agentType: string) => {
    setSelectedAgents(prev => 
      prev.includes(agentType) 
        ? prev.filter(a => a !== agentType)
        : [...prev, agentType]
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!title.trim()) {
      setError('Please enter a conversation title');
      return;
    }
    
    setIsSubmitting(true);
    setError('');
    
    try {
      const data = await createConversation({
        title: title.trim(),
        description: description.trim() || undefined,
        participants,
        agent_types: [...selectedAgents]
      });
      
      router.push(`/conversations/${data.id}`);
    } catch (err) {
      console.error('Failed to create conversation:', err);
      setError('Failed to create conversation. Please try again.');
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
    <div className="container mx-auto px-4 py-8 max-w-3xl">
      <button
        onClick={() => router.back()}
        className="flex items-center text-blue-600 mb-6 hover:underline"
      >
        <ArrowLeft size={16} className="mr-1" />
        Back
      </button>
      
      <h1 className="text-2xl font-bold mb-6">Create New Conversation</h1>
      
      <form onSubmit={handleSubmit} className="space-y-6">
        {error && (
          <div className="bg-red-50 text-red-700 p-3 rounded-md">
            {error}
          </div>
        )}
        
        <div>
          <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-1">
            Title *
          </label>
          <input
            type="text"
            id="title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full p-2 border border-gray-300 rounded-md"
            placeholder="Enter conversation title"
            required
          />
        </div>
        
        <div>
          <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
            Description (optional)
          </label>
          <textarea
            id="description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="w-full p-2 border border-gray-300 rounded-md"
            rows={3}
            placeholder="Enter a brief description of this conversation"
          />
        </div>
        
        <div>
          <h3 className="text-lg font-medium mb-3">Select AI Agents</h3>
          <p className="text-sm text-gray-500 mb-4">
            Choose which specialized AI agents to include in this conversation
          </p>
          <div className="grid sm:grid-cols-2 gap-3">
            {availableAgents.map((agent) => (
              <div 
                key={agent.type}
                className={`border rounded-md p-3 cursor-pointer transition-colors ${
                  selectedAgents.includes(agent.type) 
                    ? 'bg-blue-50 border-blue-300' 
                    : 'border-gray-300 hover:bg-gray-50'
                }`}
                onClick={() => toggleAgent(agent.type)}
              >
                <div className="flex items-start">
                  <input
                    type="checkbox"
                    checked={selectedAgents.includes(agent.type)}
                    onChange={() => {}} // Handled by div click
                    className="mt-1 mr-3"
                  />
                  <div>
                    <div className="font-medium">{agent.label}</div>
                    <div className="text-sm text-gray-500">{agent.description}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
        
        <div>
          <h3 className="text-lg font-medium mb-3">Add Participants (optional)</h3>
          
          <div className="flex items-start space-x-2 mb-4">
            <div className="flex-1">
              <input
                type="email"
                value={newParticipantEmail}
                onChange={(e) => setNewParticipantEmail(e.target.value)}
                className="w-full p-2 border border-gray-300 rounded-md mb-2"
                placeholder="Email address"
              />
              <input
                type="text"
                value={newParticipantName}
                onChange={(e) => setNewParticipantName(e.target.value)}
                className="w-full p-2 border border-gray-300 rounded-md"
                placeholder="Name (optional)"
              />
            </div>
            <Button 
              type="button" 
              onClick={addParticipant}
              className="flex-shrink-0 mt-1"
            >
              <Plus size={16} className="mr-1" />
              Add
            </Button>
          </div>
          
          {participants.length > 0 && (
            <div className="border rounded-md p-3 bg-gray-50">
              <h4 className="font-medium mb-2">Participants</h4>
              <ul className="space-y-2">
                {participants.map((participant) => (
                  <li 
                    key={participant.email}
                    className="flex justify-between items-center bg-white p-2 rounded border"
                  >
                    <div>
                      <div>{participant.name || participant.email}</div>
                      {participant.name && (
                        <div className="text-sm text-gray-500">{participant.email}</div>
                      )}
                    </div>
                    <button
                      type="button"
                      onClick={() => removeParticipant(participant.email)}
                      className="text-gray-400 hover:text-red-500"
                      aria-label="Remove participant"
                    >
                      <X size={16} />
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
        
        <div className="flex justify-end pt-4">
          <Button
            type="button"
            variant="outline"
            onClick={() => router.push('/conversations')}
            className="mr-3"
            disabled={isSubmitting}
          >
            Cancel
          </Button>
          <Button 
            type="submit" 
            disabled={isSubmitting || !title.trim()}
          >
            {isSubmitting ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-2 border-b-transparent mr-2"></div>
                Creating...
              </>
            ) : 'Create Conversation'}
          </Button>
        </div>
      </form>
    </div>
  );
}