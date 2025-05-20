// src/components/ui/error-alert.tsx
import React from 'react';
import { AlertCircle, X } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface ErrorAlertProps {
  error: string | null;
  onDismiss?: () => void;
  className?: string;
}

export function ErrorAlert({ error, onDismiss, className = '' }: ErrorAlertProps) {
  if (!error) return null;

  return (
    <Alert 
      variant="destructive" 
      className={`bg-red-50 border-red-200 text-red-800 animate-in fade-in duration-300 ${className}`}
    >
      <div className="flex items-start gap-2">
        <AlertCircle className="h-4 w-4 mt-1 flex-shrink-0" />
        <AlertDescription className="flex-1 text-red-800">
          {error}
        </AlertDescription>
        {onDismiss && (
          <button
            onClick={onDismiss}
            className="p-1 hover:bg-red-100 rounded-full transition-colors flex-shrink-0"
            aria-label="Dismiss error"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>
    </Alert>
  );
}
