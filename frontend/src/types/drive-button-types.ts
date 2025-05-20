
export interface ImportProgress {
  totalFiles: number;
  processedFiles: number;
  failedFiles: number;
}

export interface DriveButtonProps {
  threadId?: string;
  isProUser: boolean;
}
