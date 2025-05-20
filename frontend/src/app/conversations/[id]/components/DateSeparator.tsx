import React from 'react';
import { formatDateSeparator } from '../utils/date.utils';

interface DateSeparatorProps {
  timestamp: string;
}

export const DateSeparator: React.FC<DateSeparatorProps> = ({ timestamp }) => {
  return (
    <div className="flex items-center my-4">
      <div className="flex-grow border-t border-gray-300"></div>
      <div className="mx-4 text-sm text-gray-500">
        {formatDateSeparator(timestamp)}
      </div>
      <div className="flex-grow border-t border-gray-300"></div>
    </div>
  );
};
