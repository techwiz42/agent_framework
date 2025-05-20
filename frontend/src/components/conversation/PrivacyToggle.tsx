import React from 'react';
import { Eye, EyeOff } from 'lucide-react';
import { useToast } from '@/components/ui/use-toast';
import { websocketService } from '@/services/websocket';

interface PrivacyToggleProps {
  conversationId: string;
  isEnabled?: boolean;
  onToggle?: (enabled: boolean) => void;
}

export function PrivacyToggle({ 
  conversationId, 
  isEnabled: propIsEnabled, 
  onToggle 
}: PrivacyToggleProps) {
  const [isPrivate, setIsPrivate] = React.useState(propIsEnabled || false);
  const { toast } = useToast();

  const handlePrivacyToggle = (e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent triggering card click
    
    const newPrivacyState = !isPrivate;
    
    try {
      websocketService.setPrivacy(conversationId, newPrivacyState);
      
      // Update local state if no external toggle provided
      if (onToggle) {
        onToggle(newPrivacyState);
      } else {
        setIsPrivate(newPrivacyState);
      }
      
      toast({
        title: newPrivacyState ? "Privacy Enabled" : "Privacy Disabled",
        description: newPrivacyState
          ? "No messages are saved to conversation history while privacy is enabled"
          : "Messages are saved to conversation history",
        duration: 3000
      });
    } catch (error) {
      console.error('Error toggling privacy:', error);
      toast({
        title: "Error",
        description: "Failed to update privacy setting",
        variant: "destructive"
      });
    }
  };

  // Use prop value if provided, otherwise use local state
  const isDisplayPrivate = propIsEnabled ?? isPrivate;

  return (
    <button
      onClick={handlePrivacyToggle}
      className={`p-2 rounded-full transition-colors duration-200 ${
        isDisplayPrivate
          ? 'bg-purple-100 hover:bg-purple-200 text-purple-600'
          : 'bg-gray-100 hover:bg-gray-200 text-gray-600'
      }`}
      title={isDisplayPrivate ? "Privacy Mode Enabled" : "Privacy Mode Disabled"}
    >
      {isDisplayPrivate ? (
        <EyeOff className="h-4 w-4" />
      ) : (
        <Eye className="h-4 w-4" />
      )}
    </button>
  );
}
