// @/app/conversations/[id]/components/FileDisplay.tsx
import React from 'react';
import { Pencil } from 'lucide-react';

interface FileDisplayProps {
  content: string;
  fileName?: string;
  isUserMessage?: boolean;
  onEdit?: () => void;
}

const FileDisplay: React.FC<FileDisplayProps> = ({
  content,
  fileName,
  isUserMessage = false,
  onEdit
}) => {
  // Determine if content should scroll based on line count
  const lineCount = content.split('\n').length;
  const shouldScroll = lineCount > 25;
  
  return (
    <div className={`
      rounded-lg p-4 relative text-sm w-full
      ${isUserMessage ? 'bg-blue-800 text-white' : 'bg-green-100 text-gray-900'}
    `}>
      {fileName && (
        <div className={`
          text-xs mb-2 font-medium
          ${isUserMessage ? 'text-white' : 'text-gray-600'}
        `}>
          {fileName}
        </div>
      )}
      <div className="relative w-full min-w-[500px]">
        <pre className={`
          font-mono whitespace-pre overflow-x-auto
          ${shouldScroll ? 'overflow-y-auto max-h-96' : ''}
        `}>
          <code>{content}</code>
        </pre>
      </div>
      {onEdit && (
        <button
          onClick={onEdit}
          className={`
            absolute bottom-3 right-3
            ${isUserMessage ? 'text-white hover:text-gray-200' : 'text-gray-600 hover:text-gray-900'}
          `}
          aria-label="Edit file"
        >
          <Pencil className="w-4 h-4" />
        </button>
      )}
    </div>
  );
};

export default FileDisplay;
