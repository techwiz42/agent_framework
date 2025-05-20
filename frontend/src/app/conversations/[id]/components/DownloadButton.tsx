'use client';

import { useState, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Download } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { FILE_TYPES } from '@/app/conversations/[id]/types/fileTypes';

interface DownloadButtonProps {
  content: string;
  defaultFileName?: string;
  directory?: string;
  currentFileType?: string;
}

export const DownloadButton = ({ 
  content, 
  defaultFileName = 'response',
  directory = '',
  currentFileType = 'txt'
}: DownloadButtonProps) => {
  const [fileName, setFileName] = useState(defaultFileName);
  const [fileType, setFileType] = useState(currentFileType);
  const [isOpen, setIsOpen] = useState(false);
  const downloadLinkRef = useRef<HTMLAnchorElement>(null);

  const handleNativeDownload = async () => {
    const selectedType = FILE_TYPES[fileType];
    if (!selectedType) return false;

    const processedContent = selectedType.processContent(content);

    try {
      // Check if the File System Access API is available
      if ('showSaveFilePicker' in window) {
        const handle = await window.showSaveFilePicker({
          suggestedName: `${directory ? directory + '/' : ''}${fileName}.${fileType}`,
          types: [{
            description: selectedType.description,
            accept: {
              [selectedType.mimeType]: [`.${selectedType.extension}`]
            }
          }]
        });

        const writable = await handle.createWritable();
        await writable.write(processedContent);
        await writable.close();
        setIsOpen(false);
        return true;
      }
      return false;
    } catch (error) {
      console.error('Native save failed:', error);
      return false;
    }
  };

  const handleLegacyDownload = () => {
    const selectedType = FILE_TYPES[fileType];
    if (!selectedType) return;
    
    const processedContent = selectedType.processContent(content);
    const blob = new Blob([processedContent], { type: selectedType.mimeType });
    const url = URL.createObjectURL(blob);
    
    if (downloadLinkRef.current) {
      downloadLinkRef.current.href = url;
      downloadLinkRef.current.download = `${directory ? directory + '/' : ''}${fileName}.${fileType}`;
      downloadLinkRef.current.click();
      URL.revokeObjectURL(url);
    }
  };

  const handleDownload = async () => {
    try {
      const nativeSuccess = await handleNativeDownload();
      if (!nativeSuccess) {
        handleLegacyDownload();
      }
      setIsOpen(false);
    } catch (error) {
      console.error('Download failed:', error);
      handleLegacyDownload();
      setIsOpen(false);
    }
  };

  return (
    <>
      <Dialog open={isOpen} onOpenChange={setIsOpen}>
        <DialogTrigger asChild>
          <Button 
            variant="ghost" 
            size="sm" 
            className="h-8 w-8 p-0"
          >
            <Download className="h-4 w-4" />
          </Button>
        </DialogTrigger>
        <DialogContent className="bg-gray-700 text-white">
          <DialogHeader>
            <DialogTitle>Download Response</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <span className="text-sm font-medium leading-none">File name</span>
              <Input
                id="filename"
                value={fileName}
                onChange={(e) => setFileName(e.target.value)}
                placeholder="Enter file name"
                className="bg-white text-gray-800"
              />
            </div>
            <div className="space-y-2">
              <span className="text-sm font-medium leading-none">File Type</span>
              <Select
                value={fileType}
                onValueChange={setFileType}
              >
                <SelectTrigger className="bg-white text-gray-800">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-white text-gray-800 max-h-[300px]">
                  {Object.entries(FILE_TYPES).map(([ext, config]) => (
                    <SelectItem key={ext} value={ext}>
                      {config.description} (.{ext})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <Button onClick={handleDownload} className="w-full bg-blue-500 hover:bg-blue-600 text-white">
              Download
            </Button>
          </div>
        </DialogContent>
      </Dialog>
      <a ref={downloadLinkRef} style={{ display: 'none' }} />
    </>
  );
};
