import React, { useState, useEffect } from 'react';
import { Message } from '../types/message.types';
import MessageItem from './MessageItem';

interface ResponseTimes {
  [agentId: string]: string;
}

interface Props {
  messages: Message[];
  typingStates?: {
    [identifier: string]: {
      isTyping: boolean;
      agentType?: string;
      timestamp?: string;
    };
  };
}

const formatMessageTime = (timestamp: string) => {
  const date = new Date(timestamp + 'Z');
  
  const timeZoneAbbr = new Intl.DateTimeFormat('en-US', {
    timeZoneName: 'short',
    timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone
  })
  .formatToParts(date)
  .find(part => part.type === 'timeZoneName')?.value || '';

  return `${date.toLocaleTimeString('en-US', { 
    hour: 'numeric',
    minute: '2-digit',
    hour12: true
  })} ${timeZoneAbbr}`;
};

const MessageList: React.FC<Props> = ({ messages, typingStates }) => {
  const [agentStartTimes, setAgentStartTimes] = useState<ResponseTimes>({});
  const [responseTimes, setResponseTimes] = useState<ResponseTimes>({});

  useEffect(() => {
    if (!typingStates) return;
    
    console.log('Current typing states:', typingStates);
    
    Object.entries(typingStates).forEach(([identifier, state]) => {
      if (state.isTyping && state.agentType && state.timestamp) {
        console.log('Agent started typing:', identifier, state.timestamp);
        const timestamp = state.timestamp;
        if (timestamp) {
          setAgentStartTimes(prev => {
            console.log('Updating start times:', {...prev, [identifier]: timestamp});
            return {...prev, [identifier]: timestamp};
          });
        }
      }
    });
  }, [typingStates]);

  useEffect(() => {
    messages.forEach(message => {
      if (message.sender.type === 'agent') {
        const startTime = agentStartTimes[message.sender.identifier];
        console.log('Processing agent message:', {
          messageId: message.id,
          identifier: message.sender.identifier,
          startTime,
          endTime: message.timestamp
        });
        
        if (startTime && !responseTimes[message.id]) {
          const endTime = message.timestamp;
          const diff = (new Date(endTime).getTime() - new Date(startTime).getTime()) / 1000;
          const responseTime = `${diff.toFixed(1)}s`;
          console.log('Calculated response time:', responseTime);
          setResponseTimes(prev => ({
            ...prev,
            [message.id]: responseTime
          }));
        }
      }
    });
  }, [messages, agentStartTimes, responseTimes]);

  useEffect(() => {
    console.log('Current response times:', responseTimes);
  }, [responseTimes]);

  return (
    <div className="flex flex-col space-y-4 p-4">
      {messages.map((message) => (
        <MessageItem
          key={message.id}
          message={message}
          formatDate={formatMessageTime}
          responseTime={
            message.sender.type === 'agent' 
              ? responseTimes[message.id] 
              : undefined
          }
        />
      ))}
    </div>
  );
};

export default MessageList;
