// types/onedrive.ts

export interface OneDriveFile {
  id: string;
  name: string;
  webUrl?: string;
  file?: {
    mimeType: string;
    hashes?: {
      quickXorHash?: string;
      sha1Hash?: string;
      sha256Hash?: string;
    };
  };
  mimeType?: string;
  size?: number;
  lastModifiedDateTime?: string;
  '@microsoft.graph.downloadUrl'?: string;
}

export interface OneDrivePickerOptions {
  clientId: string;
  action: "download" | "query" | "share";
  multiSelect: boolean;
  advanced: {
    filter: string;
  };
  success: (response: OneDrivePickerResponse) => void;
  cancel: () => void;
  error: (error: OneDriveError) => void;
}

export interface OneDrivePickerResponse {
  value: OneDriveFile[];
}

export interface OneDriveError {
  errorCode: string;
  message: string;
}

declare global {
  interface Window {
    OneDrive?: {
      open: (options: OneDrivePickerOptions) => void;
    };
  }
}

export interface OneDriveProcessedFile {
  id: string;
  name: string;
  mimeType: string;
  webUrl?: string;
  '@microsoft'?: {
    downloadUrl?: string;
  };
}
