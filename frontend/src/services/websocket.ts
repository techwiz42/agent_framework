import { WebSocketMessage } from '@/types/websocket.types';
import { participantStorage } from '@/lib/participantStorage';
import { MessageMetadata } from '@/app/conversations/[id]/types/message.types';
import { EditorTab } from '@/app/editor/types';

export class WebSocketService {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 2000; // ms
  private handlers: ((message: WebSocketMessage) => void)[] = [];
  private currentConnection: { 
    conversationId: string; 
    token: string; 
    connectionId: string;
  } | null = null;

  public get isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }

  // Connect to the WebSocket server
  public async connect(conversationId: string, token: string, connectionId: string): Promise<void> {
    // Always disconnect existing connection when connecting to a new conversation
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      if (this.currentConnection && this.currentConnection.conversationId !== conversationId) {
        console.log('Switching conversations, disconnecting current WebSocket');
        this.disconnect();
      } else if (this.currentConnection && this.currentConnection.conversationId === conversationId) {
        console.log('WebSocket already connected to this conversation');
        return;
      }
    }
  
    return new Promise((resolve, reject) => {
      // Store the connection information for potential reconnect
      this.currentConnection = { conversationId, token, connectionId };
    
      const wsUrl = `${process.env.NEXT_PUBLIC_WS_URL}/conversations/${conversationId}?token=${token}&connection_id=${connectionId}`;

      try {
        this.ws = new WebSocket(wsUrl);
      
        this.ws.onopen = () => {
          console.log('WebSocket connection established');
          this.reconnectAttempts = 0;
          resolve();
        };
      
        this.ws.onmessage = (event) => {
          try {
            const parsedMessage = JSON.parse(event.data) as WebSocketMessage;
            this.handlers.forEach(handler => handler(parsedMessage));
          } catch (error) {
            console.error('Error processing WebSocket message:', error);
          }
        };
      
        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          reject(error);
        };
      
        this.ws.onclose = () => {
          console.log('WebSocket connection closed');
          this.cleanup();
          this.reconnect();
        };
      } catch (error) {
        console.error('Error creating WebSocket connection:', error);
        this.cleanup();
        reject(error);
      }
    });
  }

  // Reconnect logic
  private reconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnect attempts reached');
      return;
    }

    setTimeout(() => {
      this.reconnectAttempts++;
      console.log(`Reconnecting (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
      
      // Attempt to reconnect if we have the connection info
      if (this.currentConnection) {
        this.connect(
          this.currentConnection.conversationId,
          this.currentConnection.token,
          this.currentConnection.connectionId
        ).catch(error => {
          console.error('Reconnection failed:', error);
        });
      }
    }, this.reconnectDelay);
  }

  // Clean up WebSocket resources
  private cleanup(): void {
    if (this.ws) {
      this.ws.onopen = null;
      this.ws.onmessage = null;
      this.ws.onerror = null;
      this.ws.onclose = null;
      
      if (this.ws.readyState === WebSocket.OPEN) {
        this.ws.close();
      }
      
      this.ws = null;
    }
  }

  public disconnect(): void {
    this.cleanup();
  }

  // Subscribe to messages
  public subscribe(handler: (message: WebSocketMessage) => void): () => void {
    this.handlers.push(handler);
    
    return () => {
      this.handlers = this.handlers.filter(h => h !== handler);
    };
  }

  // Send a chat message
  public sendMessage(content: string, senderEmail: string, messageMetadata?: MessageMetadata): void {
    if (!this.isConnected) {
      console.error('Cannot send message: WebSocket not connected');
      return;
    }

    const message = {
      type: 'message',
      content,
      identifier: senderEmail,
      timestamp: new Date().toISOString(),
      message_metadata: messageMetadata || {}
    };

    try {
      this.ws!.send(JSON.stringify(message));
    } catch (error) {
      console.error('Error sending message:', error);
      this.cleanup();
      this.reconnect();
    }
  }

  // Send typing status
  public sendTypingStatus(isTyping: boolean, senderEmail: string): void {
    if (!this.isConnected) {
      console.error('Cannot send typing status: WebSocket not connected');
      return;
    }

    const message = {
      type: 'typing_status',
      is_typing: isTyping,
      identifier: senderEmail,
      timestamp: new Date().toISOString()
    };

    try {
      this.ws!.send(JSON.stringify(message));
    } catch (error) {
      console.error('Error sending typing status:', error);
      this.cleanup();
      this.reconnect();
    }
  }

  public setPrivacy(conversationId: string, isPrivate: boolean): void {
    if (!this.isConnected) {
      console.error('Cannot set privacy: WebSocket not connected');
      return;
    }

    const participantSession = participantStorage.getSession(conversationId);
    const senderEmail = participantSession?.email || 'unknown';

    const message = {
      type: 'set_privacy',
      is_private: isPrivate,
      identifier: senderEmail,
      timestamp: new Date().toISOString()
    };

    try {
      this.ws!.send(JSON.stringify(message));
    } catch (error) {
      console.error('Error setting privacy:', error);
      this.cleanup();
      this.reconnect();
    }
  }

  // Editor collaboration methods
  public sendEditorOpen(tab: EditorTab): void {
    if (!this.isConnected || !this.currentConnection) {
      console.log('WebSocket not connected, editor will open in single-user mode');
      return;
    }

    const conversationId = this.currentConnection.conversationId;
    const participantSession = participantStorage.getSession(conversationId);
    if (!participantSession) {
      console.log('No participant session found, editor will open in single-user mode');
      return;
    }

    const message = {
      type: 'editor_open',
      content: tab.content,
      fileName: tab.fileName,
      fileType: tab.fileType,
      identifier: participantSession.email,
      timestamp: new Date().toISOString(),
      sender: {
        email: participantSession.email,
        name: participantSession.name
      }
    };

    try {
      this.ws!.send(JSON.stringify(message));
      console.log('Sent editor open event for collaborative editing', tab.fileName);
    } catch (error) {
      console.error('Error sending editor open event:', error);
      this.cleanup();
      this.reconnect();
    }
  }

  public sendEditorChange(tab: EditorTab): void {
    if (!this.isConnected || !this.currentConnection) {
      return; // Silent return for single-user mode
    }

    const conversationId = this.currentConnection.conversationId;
    const participantSession = participantStorage.getSession(conversationId);
    if (!participantSession) {
      return; // Silent return for single-user mode
    }

    const message = {
      type: 'editor_change',
      content: tab.content,
      fileName: tab.fileName,
      identifier: participantSession.email,
      timestamp: new Date().toISOString(),
      sender: {
        email: participantSession.email,
        name: participantSession.name
      }
    };

    try {
      console.log('Sending editor change event:', tab.fileName);
      this.ws!.send(JSON.stringify(message));
    } catch (error) {
      console.error('Error sending editor change:', error);
      this.cleanup();
      this.reconnect();
    }
  }

  public sendEditorClose(fileName: string): void {
    if (!this.isConnected || !this.currentConnection) {
      return; // Silent return for single-user mode
    }

    const conversationId = this.currentConnection.conversationId;
    const participantSession = participantStorage.getSession(conversationId);
    if (!participantSession) {
      return; // Silent return for single-user mode
    }

    const message = {
      type: 'editor_close',
      fileName: fileName,
      identifier: participantSession.email,
      timestamp: new Date().toISOString(),
      sender: {
        email: participantSession.email,
        name: participantSession.name
      }
    };

    try {
      this.ws!.send(JSON.stringify(message));
    } catch (error) {
      console.error('Error sending editor close event:', error);
      this.cleanup();
      this.reconnect();
    }
  }
}

export const websocketService = new WebSocketService();
