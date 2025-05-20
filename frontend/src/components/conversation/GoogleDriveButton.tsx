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

interface GoogleDriveFile {
  id: string;
  name: string;
  webUrl: string;
  type: string;
  mimeType: string;
}

const GoogleDriveIcon = ({ className = "h-4 w-4" }) => (
  <svg viewBox="0 0 87.3 78" className={className}>
    <path d="m6.6 66.85 3.85 6.65c.8 1.4 1.95 2.5 3.3 3.3l13.75-23.8h-27.5c0 1.55.4 3.1 1.2 4.5z" fill="#0066da"/>
    <path d="m43.65 25-13.75-23.8c-1.35.8-2.5 1.9-3.3 3.3l-25.4 44a9.06 9.06 0 0 0 -1.2 4.5h27.5z" fill="#00ac47"/>
    <path d="m73.55 76.8c1.35-.8 2.5-1.9 3.3-3.3l1.6-2.75 7.65-13.25c.8-1.4 1.2-2.95 1.2-4.5h-27.502l5.852 11.5z" fill="#ea4335"/>
    <path d="m43.65 25 13.75-23.8c-1.35-.8-2.9-1.2-4.5-1.2h-18.5c-1.6 0-3.15.45-4.5 1.2z" fill="#00832d"/>
    <path d="m59.8 53h-32.3l-13.75 23.8c1.35.8 2.9 1.2 4.5 1.2h50.8c1.6 0 3.15-.45 4.5-1.2z" fill="#2684fc"/>
    <path d="m73.4 26.5-12.7-22c-.8-1.4-1.95-2.5-3.3-3.3l-13.75 23.8 16.15 28h27.45c0-1.55-.4-3.1-1.2-4.5z" fill="#ffba00"/>
  </svg>
);

interface GoogleDriveButtonProps {
  onFilesSelected?: (files: GoogleDriveFile[], accessToken: string, refreshToken: string) => void;
}

const GoogleDriveButton = ({ onFilesSelected }: GoogleDriveButtonProps) => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [authWindow, setAuthWindow] = useState<Window | null>(null);
  const [files, setFiles] = useState<GoogleDriveFile[]>([]);
  const [selectedFiles, setSelectedFiles] = useState<Set<string>>(new Set());
  const [showFileDialog, setShowFileDialog] = useState(false);
  const [accessToken, setAccessToken] = useState<string>('');
  const [refreshToken, setRefreshToken] = useState<string>('');
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
      
      // Get the authentication token
      const authToken = authService.getToken();
          
      if (!authToken) {
          throw new Error('Not authenticated');
      } 
      
      // Send to backend for processing
      const response = await fetch('/api/google/ingest', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({
          access_token: accessToken,
          refresh_token: refreshToken,
          files: filesToIngest
        }),
      });
      
      if (!response.ok) {
        let errorMessage = `Failed to ingest Google Drive files: ${response.status} ${response.statusText}`;
        try {
          const errorData = await response.json();
          if (errorData.detail) {
            errorMessage = typeof errorData.detail === 'string' 
              ? errorData.detail 
              : errorData.detail.message || JSON.stringify(errorData.detail);
          }
        } catch (parseError) {
          console.error('Error parsing error response:', parseError);
          const errorText = await response.text();
          errorMessage += ` - ${errorText.substring(0, 100)}`;
        }
        
        throw new Error(errorMessage);
      }
      
      const result = await response.json();
      
      toast({
        title: 'Files Indexed Successfully',
        description: `${result.stats?.processed_files || 0} files processed, ${result.stats?.failed_files || 0} failed`,
        variant: 'default',
      });
      
      // Call the callback if provided
      if (onFilesSelected) {
        onFilesSelected(filesToIngest, accessToken, refreshToken || '');
      }
      
    } catch (error) {
      console.error('Error ingesting Google Drive files:', error);
      toast({
        title: 'Indexing Failed',
        description: error instanceof Error ? error.message : 'Failed to index Google Drive files',
        variant: 'destructive',
      });
    } finally {
      setIsProcessing(false);
      setSelectedFiles(new Set());
    }
  }, [selectedFiles, files, accessToken, refreshToken, toast, onFilesSelected]);

  // Handle OAuth messages from the popup window
  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      // Ensure the message is from our domain
      if (event.origin !== window.location.origin) return;

      const data = event.data;
      
      // Handle successful OAuth
      if (data && data.type === 'google_oauth_success') {
        console.log('Received OAuth success message');
        
        // Get tokens
        const accessToken = data.access_token;
        const refreshToken = data.refresh_token || '';
        
        if (!accessToken) {
          console.error('No access token received');
          toast({
            title: "Authentication Failed",
            description: "No access token received from Google",
            variant: "destructive"
          });
          setIsProcessing(false);
          return;
        }

        // Store tokens
        setAccessToken(accessToken);
        setRefreshToken(refreshToken);
        
        // Warn if no refresh token
        if (!refreshToken) {
          console.warn("No refresh token received - token access may expire sooner");
          toast({
            title: "Limited Access",
            description: "Access may expire after one hour. You may need to re-authenticate later.",
            variant: "destructive"
          });
        }

        toast({
          title: 'Connected to Google Drive',
          description: 'Fetching files...',
          variant: 'default',
        });

        // Get authentication token
        const authToken = authService.getToken();
        
        // List files from Google Drive
        console.log("Fetching files with access token");
        fetch('/api/google/files', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`
          },
          body: JSON.stringify({ access_token: accessToken }),
        })
        .then(response => {
          if (!response.ok) {
            throw new Error(response.statusText || 'Failed to fetch files');
          }
          return response.json();
        })
        .then(data => {
          const filesData = data.files || [];
          console.log(`Retrieved ${filesData.length} files from Google Drive`);
          
          if (filesData.length > 0) {
            // Store files and show selection dialog
            setFiles(filesData);
            setShowFileDialog(true);
          } else {
            toast({
              title: "No compatible files found",
              description: "No supported files were found in your Google Drive",
              variant: "default"
            });
          }
          setIsProcessing(false);
        })
        .catch(error => {
          console.error('Error fetching files:', error);
          toast({
            title: "Error",
            description: error instanceof Error ? error.message : "Failed to load files from Google Drive",
            variant: "destructive"
          });
          setIsProcessing(false);
        });
      }

      // Handle OAuth errors
      if (data && data.type === 'google_oauth_error') {
        console.error('OAuth error:', data.error);
        setIsProcessing(false);
        toast({
          title: "Authentication Failed",
          description: data.error || "Failed to authenticate with Google Drive",
          variant: "destructive"
        });
      }
    };

    // Add event listener for messages from the popup
    window.addEventListener('message', handleMessage);

    // Clean up event listener
    return () => {
      window.removeEventListener('message', handleMessage);
    };
  }, [toast]);

  const handleClick = () => {
    setIsProcessing(true);
    
    // Define popup dimensions and position
    const width = 500;
    const height = 600;
    const left = window.screenX + (window.outerWidth - width) / 2;
    const top = window.screenY + (window.outerHeight - height) / 2;
    
    // Close any existing window
    if (authWindow && !authWindow.closed) {
      authWindow.close();
    }
    
    // Open the authorization popup
    const newWindow = window.open(
      '/api/oauth/google/authorize',
      'Google Drive Authorization',
      `width=${width},height=${height},left=${left},top=${top}`
    );
    
    setAuthWindow(newWindow);
    
    // Handle if popup is blocked
    if (!newWindow || newWindow.closed || typeof newWindow.closed === 'undefined') {
      setIsProcessing(false);
      toast({
        title: "Popup Blocked",
        description: "Please allow popups for this site to use Google Drive integration",
        variant: "destructive"
      });
    }
    
    // Set a timeout to detect if auth flow didn't complete
    const timeout = setTimeout(() => {
      if (isProcessing) {
        setIsProcessing(false);
        toast({
          title: "Authentication Timeout",
          description: "The authentication process took too long. Please try again.",
          variant: "default"
        });
      }
    }, 120000); // 2 minute timeout
    
    return () => clearTimeout(timeout);
  };

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
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Processing...
          </>
        ) : (
          <>
            <GoogleDriveIcon className="h-5 w-5" />
            Index Google Drive Files
          </>
        )}
      </Button>
      
      {/* File Selection Dialog */}
      <Dialog open={showFileDialog} onOpenChange={setShowFileDialog}>
        <DialogContent className="max-w-md max-h-[80vh] overflow-y-auto backdrop-blur-md bg-white/90 dark:bg-gray-950/90 border border-gray-200 dark:border-gray-800 shadow-lg">
          <DialogHeader>
            <DialogTitle>Select Google Drive Files to Index</DialogTitle>
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

export default GoogleDriveButton;
