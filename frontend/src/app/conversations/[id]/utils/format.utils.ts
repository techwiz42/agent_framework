export const formatAgentName = (agentType: string): string => {
  return agentType
    .toLowerCase()
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
};

export const getMessageClassName = (
  type: 'user' | 'agent' | 'moderator',
  isOwner: boolean
): string => {
  const baseClasses = 'rounded-lg px-4 py-2 max-w-[70%]';
  
  if (type === 'user') {
    return `${baseClasses} ${
      isOwner 
        ? 'bg-blue-500 text-white'
        : 'bg-gray-100'
    }`;
  }
  
  if (type === 'agent') {
    return `${baseClasses} bg-green-100 border border-green-300`;
  }
  
  return `${baseClasses} bg-gray-50 border border-gray-200`;
};
