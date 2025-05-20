'use client';

import React, { useEffect, useState } from 'react';

// Define TypeScript interfaces for token response
interface TokenResponse {
  access_token: string;
  refresh_token?: string;
  expires_in: number;
  scope: string;
  token_type: string;
}

interface ErrorResponse {
  detail: string;
}

export default function GoogleCallback() {
  const [status, setStatus] = useState('Processing Google Drive Authorization...');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const handleCallback = async () => {
      try {
        // Use URL search params for authorization code flow
        const urlParams = new URLSearchParams(window.location.search);
        const code = urlParams.get('code');
        const state = urlParams.get('state');
        const urlError = urlParams.get('error');

        console.log('Received OAuth callback with:', {
          code: code ? `${code.substring(0, 10)}...` : 'No code',
          state: state ? `${state.substring(0, 10)}...` : 'No state',
          error: urlError
        });

        if (urlError || !code || !state) {
          throw new Error(urlError || 'No authorization code or state received');
        }

        setStatus('Exchanging code for access token...');

        // Exchange code for token
        const response = await fetch('/api/oauth/google/token', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            code: code,
            redirect_uri: 'https://agentframework.ai/google-callback',
            state: state
          }),
        });

        if (!response.ok) {
          const errorData = await response.json() as ErrorResponse;
          console.error('Token exchange failed:', response.status, errorData);
          throw new Error(
            errorData?.detail || 
            `Failed to exchange code for token: ${response.status} ${response.statusText}`
          );
        }

        const tokenData = await response.json() as TokenResponse;
        console.log('Token exchange successful, received keys:', Object.keys(tokenData));
        
        // Check for access token at minimum
        if (!tokenData.access_token) {
          throw new Error('No access token received');
        }

        // Warn if no refresh token, but don't fail
        if (!tokenData.refresh_token) {
          console.warn('No refresh token received - this may cause issues with long-term access');
        }

        setStatus('Authorization successful! Returning to app...');

        // Pass token data back to the opener window
        if (window.opener) {
          window.opener.postMessage({
            type: 'google_oauth_success',
            access_token: tokenData.access_token,
            refresh_token: tokenData.refresh_token || '',
            expires_in: tokenData.expires_in,
            scope: tokenData.scope
          }, window.location.origin);
          
          // Close the window after a short delay
          setTimeout(() => {
            window.close();
          }, 500);
        } else {
          setStatus('Authorization successful, but opener window not found.');
          setError('Please return to the main application.');
        }

      } catch (error) {
        console.error('Google OAuth Error:', error);
        setStatus('Authorization failed');
        setError(error instanceof Error ? error.message : 'Unknown error');
        
        if (window.opener) {
          window.opener.postMessage({
            type: 'google_oauth_error',
            error: error instanceof Error ? error.message : 'Unknown error'
          }, window.location.origin);
          
          // Close the window after showing the error
          setTimeout(() => {
            window.close();
          }, 3000);
        }
      }
    };

    handleCallback();
  }, []);

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-50">
      <div className="text-center p-6 bg-white rounded-lg shadow-md max-w-md w-full">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto mb-4"></div>
        <h1 className="text-xl font-semibold mb-2">{status}</h1>
        
        {error && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-md">
            <p className="font-medium mb-1">Error</p>
            <p>{error}</p>
          </div>
        )}
        
        <div className="mt-6 text-sm text-gray-500">
          <p>Debug Information:</p>
          <ul className="mt-2 list-disc list-inside text-left">
            <li>Origin: {window.location.origin}</li>
            <li>URL Path: {window.location.pathname}</li>
            <li>Has Hash: {window.location.hash ? 'Yes' : 'No'}</li>
            <li>Has Search Params: {window.location.search ? 'Yes' : 'No'}</li>
            <li>Has Opener: {window.opener ? 'Yes' : 'No'}</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
