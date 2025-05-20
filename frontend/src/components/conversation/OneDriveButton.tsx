import { useState, useEffect, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Loader2 } from 'lucide-react';
import { useToast } from '@/components/ui/use-toast';
import { authService } from '@/services/auth';
import { 
  Dialog, 
  DialogContent, 
  DialogHeader, 
  DialogTitle,
  DialogDescription
} from '@/components/ui/dialog';

interface OneDriveFile {
  id: string;
  name: string;
  mimeType: string;
  webUrl?: string;
  microsoft?: {
    downloadUrl: string;
  };
}

interface OneDriveButtonProps {
  availableTokens?: number;
  onFilesSelected?: (files: OneDriveFile[], accessToken: string) => void;
}

const OneDriveIcon = () => (
  <svg viewBox="0 0 24 24" className="h-5 w-5 text-blue-500" fill="currentColor">
    <path d="M19.453 8.969c-.999-.445-2.102-.694-3.266-.694-3.037 0-5.686 1.708-7.031 4.215-1.19-.921-2.691-1.474-4.32-1.474-.387 0-.766.034-1.133.098C3.262 11.193 3 11.364 3 11.628v6.695c0 .322.261.583.583.583h16.834c.322 0 .583-.261.583-.583v-7.164c0-.322-.261-.583-.583-.583h-.746c-.218 0-.421.114-.534.301-.824 1.371-2.302 2.281-3.989 2.281-2.595 0-4.702-2.107-4.702-4.702 0-2.595 2.107-4.702 4.702-4.702 1.729 0 3.239.934 4.057 2.322.111.188.314.303.534.303h.746c.322 0 .583-.261.583-.583v-.801c0-.264-.262-.435-.703-.514z"/>
  </svg>
);

const OneDriveButton = ({ onFilesSelected }: OneDriveButtonProps) => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [files, setFiles] = useState<OneDriveFile[]>([]);
  const [selectedFiles, setSelectedFiles] = useState<Set<string>>(new Set());
  const [showFileDialog, setShowFileDialog] = useState(false);
  const [accessToken, setAccessToken] = useState<string>('');
  const { toast } = useToast();

  // Handle file selection
  const handleFileSelection = useCallback((fileId: string) => {
    setSelectedFiles(prev => {
      const updated = new Set(prev);
      if (updated.has(fileId)) {
        updated.delete(fileId);
      } else {
        updated.add(fileId);
      }
      return updated;
    });
  }, []);

  // Function to fetch files from OneDrive
  const fetchOneDriveFiles = useCallback(async (token: string) => {
    try {
      setIsProcessing(true);
      console.log('Fetching OneDrive files with token');
      
      // Call Microsoft Graph API directly 
      const response = await fetch('https://graph.microsoft.com/v1.0/me/drive/root/children', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error?.message || 'Failed to fetch OneDrive files');
      }
      
      const data = await response.json();
      console.log('OneDrive files:', data);
      
      // Define interface for the OneDrive API response
      interface OneDriveApiFile {
        id: string;
        name: string;
        webUrl?: string;
        file?: {
          mimeType: string;
        };
        folder?: {
          childCount: number;
        };
        '@microsoft.graph.downloadUrl'?: string;
      }
      
      // Filter to only include supported file types
      const supportedFiles = (data.value as OneDriveApiFile[])
        .filter((file) => 
          !file.folder && 
          file.name && 
          file.id &&
          file.file && 
          file['@microsoft.graph.downloadUrl']
        )
        .map((file) => ({
          id: file.id,
          name: file.name,
          mimeType: file.file?.mimeType || 'application/octet-stream',
          webUrl: file.webUrl,
          microsoft: {
            downloadUrl: file['@microsoft.graph.downloadUrl'] || ''
          }
        }));
      
      console.log(`Found ${supportedFiles.length} supported files`);
      
      if (supportedFiles.length === 0) {
        toast({
          title: 'No Files Found',
          description: 'No supported files were found in your OneDrive.',
          variant: 'default',
        });
        setIsProcessing(false);
        return;
      }
      
      // Store the files and token for selection dialog
      setFiles(supportedFiles);
      setAccessToken(token);
      setShowFileDialog(true);
      setIsProcessing(false); // Important: Stop processing indicator once files are loaded
      
    } catch (error) {
      console.error('Error fetching OneDrive files:', error);
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to fetch OneDrive files',
        variant: 'destructive',
      });
      setIsProcessing(false);
    }
  }, [toast]);

  // Handle file ingestion
  const handleIngestFiles = useCallback(async () => {
    if (selectedFiles.size === 0) {
      toast({
        title: 'No Files Selected',
        description: 'Please select at least one file to index.',
        variant: 'default',
      });
      return;
    }

    try {
      setIsProcessing(true);
      setShowFileDialog(false);
      
      // Get selected files
      const filesToIngest = files.filter(file => selectedFiles.has(file.id));
      
      console.log("Sending files to backend:", filesToIngest);
      console.log("Using token:", accessToken.substring(0, 10) + "...");
      
      // From your main.py, the onedrive_router is registered with:
      // app.include_router(onedrive_router, prefix="/api") 
      // So the correct path should be just '/api/onedrive/ingest'
      // The previous version had duplicated '/api' in the path
      const ingestEndpoint = '/api/onedrive/ingest';
      
      console.log("Using endpoint:", ingestEndpoint);
      // Get the authentication token either from context or service
      const authToken = authService.getToken();
          
      if (!authToken) {
          throw new Error('Not authenticated');
      } 
      // Send to backend for processing
      const response = await fetch(ingestEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
	  'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({
          onedrive_token: accessToken,
          files: filesToIngest
        }),
      });
      
      if (!response.ok) {
        let errorMessage = `Failed to ingest OneDrive files: ${response.status} ${response.statusText}`;
        try {
          const errorData = await response.json();
          if (errorData.detail) {
            errorMessage = typeof errorData.detail === 'string' 
              ? errorData.detail 
              : errorData.detail.message || JSON.stringify(errorData.detail);
          }
        } catch (parseError) {
          console.error('Error parsing error response:', parseError);
          // If we can't parse the response, use the text instead
          const errorText = await response.text();
          errorMessage += ` - ${errorText.substring(0, 100)}`;
        }
        
        throw new Error(errorMessage);
      }
      
      const result = await response.json();
      
      toast({
        title: 'Files Indexed Successfully',
        description: `${result.processed_count} files processed, ${result.failed_count} failed`,
        variant: 'default',
      });
      
      // Call the callback if provided
      if (onFilesSelected) {
        onFilesSelected(filesToIngest, accessToken);
      }
      
    } catch (error) {
      console.error('Error ingesting OneDrive files:', error);
      toast({
        title: 'Indexing Failed',
        description: error instanceof Error ? error.message : 'Failed to index OneDrive files',
        variant: 'destructive',
      });
    } finally {
      setIsProcessing(false);
      setSelectedFiles(new Set());
    }
  }, [selectedFiles, files, accessToken, toast, onFilesSelected]);

  const handleClick = useCallback(() => {
    setIsProcessing(true);
    
    const width = 500;
    const height = 600;
    const left = window.screenX + (window.outerWidth - width) / 2;
    const top = window.screenY + (window.outerHeight - height) / 2;
    
    const authWindow = window.open(
      '/api/oauth/onedrive/authorize',
      'OneDrive Login',
      `width=${width},height=${height},left=${left},top=${top}`
    );
    
    // Set timeout to detect if auth flow didn't complete
    const timeout = setTimeout(() => {
      if (isProcessing) {
        setIsProcessing(false);
        toast({
          title: 'Authentication Timeout',
          description: 'The authentication process took too long. Please try again.',
          variant: 'default',
        });
        if (authWindow && !authWindow.closed) {
          authWindow.close();
        }
      }
    }, 120000); // 2 minute timeout
    
    return () => clearTimeout(timeout);
  }, [isProcessing, toast]);

  useEffect(() => {
    const handleOAuthMessage = (event: MessageEvent<unknown>) => {
      if (event.origin !== window.location.origin) return;
      
      // Type guard to check if event.data has the expected structure
      if (typeof event.data === 'object' && event.data !== null && 'type' in event.data && event.data.type === 'onedrive_oauth_success') {
        try {
          console.log('OneDrive OAuth success:', event.data);
          
          // Safely access nested properties with type validation
          const eventData = event.data as { 
            type: string; 
            data?: { 
              access_token?: string 
            } 
          };
          const token = eventData.data?.access_token;
          
          if (!token) {
            throw new Error('No access token received');
          }
          
          toast({
            title: 'Connected to OneDrive',
            description: 'Fetching files...',
            variant: 'default',
          });
          
          // Make a call to Microsoft Graph API to list files
          // Since we now have CSP permissions for Microsoft Graph
          fetchOneDriveFiles(token);
          
        } catch (error) {
          console.error('Error handling OneDrive files:', error);
          toast({
            title: 'Error',
            description: error instanceof Error ? error.message : 'Failed to process OneDrive files',
            variant: 'destructive',
          });
          setIsProcessing(false);
        }
      }
      
      if (typeof event.data === 'object' && event.data !== null && 'type' in event.data && event.data.type === 'onedrive_oauth_error') {
        const errorData = event.data as { type: string; error: string };
        console.error('OneDrive OAuth error:', errorData.error);
        toast({
          title: 'Connection Failed',
          description: `Failed to connect OneDrive: ${errorData.error}`,
          variant: 'destructive',
        });
        setIsProcessing(false);
      }
    };

    window.addEventListener('message', handleOAuthMessage);
    return () => window.removeEventListener('message', handleOAuthMessage);
  }, [toast, fetchOneDriveFiles]);

  return (
    <>
      <Button 
        variant="outline" 
        onClick={handleClick}
        disabled={isProcessing}
        className="flex items-center gap-2"
      >
        {isProcessing ? (
          <>
            <Loader2 className="h-4 w-4 animate-spin" />
            Processing...
          </>
        ) : (
          <>
            <OneDriveIcon />
            Index OneDrive Files
          </>
        )}
      </Button>
      
      {/* File Selection Dialog */}
      <Dialog open={showFileDialog} onOpenChange={setShowFileDialog}>
        <DialogContent className="max-w-md max-h-[80vh] overflow-y-auto backdrop-blur-md bg-white/90 dark:bg-gray-950/90 border border-gray-200 dark:border-gray-800 shadow-lg">
          <DialogHeader>
            <DialogTitle>Select OneDrive Files to Index</DialogTitle>
            <DialogDescription>
              Choose the files you want to add to your knowledge base.
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 my-4">
            {files.length === 0 ? (
              <div className="text-center text-gray-500">No files found</div>
            ) : (
              <>
                <div className="flex justify-between mb-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setSelectedFiles(new Set(files.map(f => f.id)))}
                  >
                    Select All
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setSelectedFiles(new Set())}
                  >
                    Clear
                  </Button>
                </div>
                
                <div className="space-y-2 max-h-[40vh] overflow-y-auto pr-2">
                  {files.map(file => (
                    <div 
                      key={file.id} 
                      className={`flex items-center p-2 rounded cursor-pointer transition-colors ${
                        selectedFiles.has(file.id) ? 'bg-blue-100 dark:bg-blue-900/30' : 'hover:bg-gray-100 dark:hover:bg-gray-800/50'
                      }`}
                      onClick={() => handleFileSelection(file.id)}
                    >
                      <div className="flex-shrink-0 mr-2 w-5 h-5 border border-gray-300 dark:border-gray-600 rounded flex items-center justify-center">
                        {selectedFiles.has(file.id) && (
                          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <polyline points="20 6 9 17 4 12"></polyline>
                          </svg>
                        )}
                      </div>
                      <div className="flex-1">
                        <div className="font-medium text-sm">{file.name}</div>
                        <div className="text-xs text-gray-500">{file.mimeType}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>
          
          <div className="flex justify-end space-x-2">
            <Button
              variant="outline"
              onClick={() => {
                setShowFileDialog(false);
                setSelectedFiles(new Set());
              }}
              disabled={isProcessing}
              className="bg-yellow-100 hover:bg-yellow-200 border-yellow-300 text-yellow-800"
            >
              Cancel
            </Button>
            <Button
              onClick={handleIngestFiles}
              disabled={selectedFiles.size === 0 || isProcessing}
              className="bg-green-600 hover:bg-green-700 text-white"
            >
              {isProcessing ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Indexing...
                </>
              ) : (
                `Index ${selectedFiles.size} Files`
              )}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
};

export default OneDriveButton;
