'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { conversationService } from '@/services/conversations';
import { agentService } from '@/services/agents';
import { MainLayout } from '@/components/layout/MainLayout';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent } from '@/components/ui/card';
import { ErrorAlert } from '@/components/ui/error-alert';
import { isValidEmail } from '@/lib/validation';
import { toast } from '@/components/ui/use-toast';
import { HelpCircle, ChevronDown, ChevronUp } from 'lucide-react';

interface ConversationFormState {
  title: string;
  description: string;
  selectedAgents: string[];
  participantEmails: string;
}

interface AgentButtonProps {
  agent: string;
  description: string;
  isSelected: boolean;
  onToggle: () => void;
  disabled: boolean;
}

const AgentButton = ({ 
  agent, 
  description, 
  isSelected, 
  onToggle, 
  disabled 
}: AgentButtonProps) => {
  const formatAgentName = (agent: string): string => {
    return agent
      .toLowerCase()
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  const showAgentInfo = () => {
    toast({
      title: formatAgentName(agent),
      description: description,
      duration: 5000
    });
  };

  return (
    <div className="relative">
      <Button
        type="button"
        variant={isSelected ? "default" : "outline"}
        onClick={onToggle}
        className={`justify-start w-full pr-10 ${
          disabled
            ? 'bg-gray-200 cursor-not-allowed'
            : isSelected
              ? 'bg-green-100 hover:bg-green-200 border-green-500'
              : ''
        }`}
        disabled={disabled}
      >
        {formatAgentName(agent)}
      </Button>
      
      <button
        type="button"
        onClick={(e) => {
          e.preventDefault();
          e.stopPropagation();
          showAgentInfo();
        }}
        className="absolute right-1 top-1/2 -translate-y-1/2 h-8 w-8 p-0 hover:bg-gray-100 rounded-full flex items-center justify-center"
      >
        <HelpCircle className="h-4 w-4 text-blue-500" />
      </button>
    </div>
  );
};

export default function CreateConversationPage() {
  const router = useRouter();
  const { token } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [availableAgents, setAvailableAgents] = useState<string[]>([]);
  const [agentDescriptions, setAgentDescriptions] = useState<Record<string, string>>({});
  const [showAllAgents, setShowAllAgents] = useState(false);

  // List of initially visible agents - AGENT_FRAMEWORK_GUIDE added at the beginning
  const priorityAgents = [
    'AGENT_FRAMEWORK_GUIDE', 'LEGAL', 'MEDICAL', 'BUSINESS', 'SUMMARY', 
    'ENVIRONMENTAL', 'EXECUTIVEASSISTANT', 'CODEMONKEY', 'DOCUMENTSEARCH'
  ];

  const [formData, setFormData] = useState<ConversationFormState>({
    title: '',
    description: '',
    selectedAgents: ['MODERATOR', 'MONITOR'],
    participantEmails: ''
  });

  useEffect(() => {
    const fetchAgentData = async () => {
      if (!token) {
        console.error('Token is missing. Unable to fetch agents.');
        return;
      }

      try {
        // First get the available agents
        const agents = await agentService.getAvailableAgents(token);
        setAvailableAgents(agents);
        
        // Then get descriptions
        const descriptions = await agentService.getAgentDescriptions(token);
        setAgentDescriptions(descriptions);
      } catch (error) {
        console.error('Error fetching agent data:', error);
        setError('Unable to load available agents. Please try again.');
      }
    };

    fetchAgentData();
  }, [token]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) {
      setError('You must be logged in to create a conversation');
      return;
    }

    const emails = formData.participantEmails
      ? formData.participantEmails
          .split(',')
          .map(email => email.trim())
          .filter(email => email.length > 0)
      : [];

    if (emails.length > 0) {
      const invalidEmails = emails.filter(email => !isValidEmail(email));
      if (invalidEmails.length > 0) {
        setError(`Invalid email addresses: ${invalidEmails.join(', ')}`);
        return;
      }
    }

    setIsLoading(true);
    setError(null);

    try {
      // Step 1: Create the conversation
      const conversationResponse = await conversationService.createConversation({
        title: formData.title,
        description: formData.description,
        selectedAgents: formData.selectedAgents,
        participantEmails: emails
      }, token);

      // Step 2: Send invitations if there are participants
      try {
        const conversationId = conversationResponse?.data?.id;
        if (conversationId) {
          if (emails.length > 0) {
            await conversationService.sendInvitations(conversationId, token);
            toast({
              title: "Success!",
              description: `Conversation created and invitations sent to ${emails.length} participant${emails.length > 1 ? 's' : ''}.`,
              variant: "default",
              duration: 5000
            });
          } else {
            toast({
              title: "Success!",
              description: "Conversation created successfully.",
              variant: "default",
              duration: 5000
            });
          }
        router.push(`/conversations/${conversationId}`);
	} else {
          toast({
            title: "Error",
            description: "Failed to retrieve conversation ID.",
            variant: "default",
          });
        }
      } catch (inviteError) {
        console.error('Error sending invitations:', inviteError);
        toast({
          title: "Partial Success",
          description: "Conversation created but there was an error sending invitations. You can resend invitations later.",
          variant: "default",
          duration: 5000
        });
        router.push('/conversations');
      }
    } catch (err) {
      console.error('Error creating conversation:', err);
      if (err instanceof Error) {
        if (err.message.includes('unauthorized')) {
          setError('Your session has expired. Please log in again.');
        } else if (err.message.includes('network')) {
          setError('Network error. Please check your connection and try again.');
        } else {
          setError(`Failed to create conversation: ${err.message}`);
        }
      } else {
        setError('An unexpected error occurred while creating the conversation');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleAgentToggle = (agent: string) => {
    if (['MODERATOR', 'MONITOR'].includes(agent)) return;

    setFormData(prev => ({
      ...prev,
      selectedAgents: prev.selectedAgents.includes(agent)
        ? prev.selectedAgents.filter(a => a !== agent)
        : [...prev.selectedAgents, agent]
    }));
  };

  // Filter agents based on showAllAgents state and remove MODERATOR and MONITOR
  const visibleAgents = availableAgents
    .filter(agent => !['MODERATOR', 'MONITOR'].includes(agent))
    .filter(agent => showAllAgents || priorityAgents.includes(agent.toUpperCase()));

  const hiddenAgentsCount = availableAgents.length - visibleAgents.length;

  return (
    <MainLayout title="Create New Conversation">
      <div className="max-w-2xl mx-auto">
        <Card>
          <CardContent className="pt-6">
            <form onSubmit={handleSubmit} className="space-y-6">
              {error && (
                <ErrorAlert
                  error={error}
                  onDismiss={() => setError(null)}
                />
              )}

              <div className="space-y-2">
                <label htmlFor="title" className="text-sm font-medium text-gray-700">
                  Title
                </label>
                <Input
                  id="title"
                  value={formData.title}
                  onChange={e => setFormData(prev => ({ ...prev, title: e.target.value }))}
                  required
                  placeholder="Enter conversation title"
                />
              </div>

              <div className="space-y-2">
                <label htmlFor="participants" className="text-sm font-medium text-gray-700">
                  Invite Participants
                </label>
                <Input
                  id="participants"
                  value={formData.participantEmails}
                  onChange={e => setFormData(prev => ({ ...prev, participantEmails: e.target.value }))}
                  placeholder="Optional: name@example.com, name2@example.com"
                />
                <p className="text-sm text-gray-500">
                  Enter email addresses separated by commas (optional)
                </p>
              </div>

              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <label className="text-sm font-medium text-gray-700">
                    Select AI Participants
                  </label>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => setShowAllAgents(!showAllAgents)}
                    className="text-blue-600 border-blue-300 hover:bg-blue-50 flex items-center gap-1"
                  >
                    {showAllAgents ? (
                      <>
                        <ChevronUp className="h-4 w-4" />
                        Hide Additional Agents
                      </>
                    ) : (
                      <>
                        <ChevronDown className="h-4 w-4" />
                        Show {hiddenAgentsCount} More Agents
                      </>
                    )}
                  </Button>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  {visibleAgents.map(agent => (
                    <AgentButton
                      key={agent}
                      agent={agent}
                      description={agentDescriptions[agent] || 'Loading description...'}
                      isSelected={formData.selectedAgents.includes(agent)}
                      onToggle={() => handleAgentToggle(agent)}
                      disabled={agent === 'MODERATOR' || agent === 'MONITOR'}
                    />
                  ))}
                </div>
                <p className="text-sm text-gray-500">
                  Moderator and Monitor agents are automatically included in every conversation
                </p>
              </div>

              <div className="space-y-2">
                <label htmlFor="description" className="text-sm font-medium text-gray-700">
                  Description
                </label>
                <Textarea
                  id="description"
                  value={formData.description}
                  onChange={e => setFormData(prev => ({ ...prev, description: e.target.value }))}
                  placeholder="Enter conversation description (optional)"
                  className="w-full min-h-[100px]"
                />
              </div>

              <div className="flex justify-end space-x-4">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => router.push('/conversations')}
                  className="bg-yellow-50 hover:bg-yellow-100 border-yellow-500 text-yellow-700"
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={isLoading}
                  className="bg-green-600 hover:bg-green-700 text-white"
                >
                  {isLoading ? 'Creating conversation...' : 'Create Conversation'}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </MainLayout>
  );
}
