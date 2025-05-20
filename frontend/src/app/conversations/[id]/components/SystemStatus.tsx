import React from 'react';
import { SystemState } from '../types/state.types';
import { formatAgentName } from '../utils/format.utils';

interface SystemStatusProps {
  systemState: SystemState;
}

export const SystemStatus: React.FC<SystemStatusProps> = ({ systemState }) => {
  const { moderatorAnalyzing, activeAgent, agentTyping } = systemState;

  if (!moderatorAnalyzing && !activeAgent) return null;

  return (
    <div className="text-sm space-y-1">
      {moderatorAnalyzing && (
        <div className="text-blue-600">
          Moderator is analyzing the conversation...
        </div>
      )}
      
      {activeAgent && agentTyping && (
        <div className="text-green-600">
          {formatAgentName(activeAgent.agent_type)} is preparing a response...
        </div>
      )}
    </div>
  );
};
