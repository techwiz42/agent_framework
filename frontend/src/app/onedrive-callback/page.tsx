'use client';

import { NextPage } from 'next';
import { useEffect, useState } from 'react';

// Define types
type TokenData = {
  access_token: string;
  token_type: string;
  expires_in: number;
  scope: string;
  state?: string;
  user_info?: Record<string, unknown>;
};

const OneDriveCallback: NextPage = () => {
  const [status, setStatus] = useState('Processing OneDrive Authentication...');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const processImplicitFlowCallback = () => {
      // Parse the URL fragment
      const hash = window.location.hash.substring(1);
      const params = new URLSearchParams(hash);

      // Extract token details
      const accessToken = params.get('access_token');
      const tokenType = params.get('token_type');
      const expiresIn = params.get('expires_in');
      const scope = params.get('scope');
      const state = params.get('state');

      // Extensive logging for debugging
      console.log('Raw URL Fragment:', hash);
      console.log('Access Token (partial):', accessToken ? `${accessToken.substring(0, 20)}...` : 'No token');
      console.log('Token Type:', tokenType);
      console.log('Expires In:', expiresIn);
      console.log('Scope:', scope);

      // Validate token presence
      if (!accessToken || !tokenType) {
        const errorMessage = 'Authentication failed: Missing essential tokens';
        console.error(errorMessage);
        setError(errorMessage);
        
        // Notify the opener about the error
        if (window.opener) {
          window.opener.postMessage({
            type: 'onedrive_oauth_error',
            error: errorMessage
          }, window.location.origin);
          
          setTimeout(() => window.close(), 3000);
        }
        return;
      }

      // Prepare token data
      const tokenData: TokenData = {
        access_token: accessToken,
        token_type: tokenType,
        expires_in: expiresIn ? parseInt(expiresIn) : 3600,
        scope: scope || '',
        state: state || undefined
      };

      // Validate token with Microsoft Graph API
      const validateToken = async () => {
        try {
          console.log('Attempting to validate token...');
          const response = await fetch('https://graph.microsoft.com/v1.0/me', {
            headers: {
              'Authorization': `Bearer ${accessToken}`,
              'Accept': 'application/json'
            }
          });

          console.log('Token Validation Response Status:', response.status);

          if (!response.ok) {
            const errorText = await response.text();
            console.error('Token Validation Error:', errorText);
            throw new Error(`Token validation failed: ${errorText}`);
          }

          const userProfile = await response.json();
          console.log('User Profile:', JSON.stringify(userProfile, null, 2));

          // Send token data back to opener window
          if (window.opener) {
            window.opener.postMessage({
              type: 'onedrive_oauth_success',
              data: {
                ...tokenData,
                user_info: userProfile
              }
            }, window.location.origin);

            setStatus('Authentication successful. Closing window...');
            
            // Auto-close the window after a short delay
            setTimeout(() => {
              window.close();
            }, 500);
          } else {
            setError('No opener window found');
          }
        } catch (validationError) {
          console.error('Token validation failed:', validationError);
          setError(validationError instanceof Error ? validationError.message : 'Unknown validation error');
          
          // If there's a CORS error due to CSP restrictions, fall back to just sending the token back
          if (validationError instanceof TypeError && 
              (validationError.message.includes('NetworkError') || 
               validationError.message.includes('Failed to fetch'))) {
            console.log('CORS error detected, skipping validation and sending token back');
            setStatus('CORS/NetworkError detected. Keeping window open for debugging.');
            setError(`CORS/Network Error: ${validationError.message}\n\nCSP likely blocked direct access to Microsoft Graph API. Will NOT auto-close for debugging.`);
            
            // Still notify the opener, but don't close the window
            if (window.opener) {
              window.opener.postMessage({
                type: 'onedrive_oauth_success',
                data: tokenData
              }, window.location.origin);
            }
          } else {
            // Notify the opener about the error
            if (window.opener) {
              window.opener.postMessage({
                type: 'onedrive_oauth_error',
                error: validationError instanceof Error ? validationError.message : 'Unknown validation error'
              }, window.location.origin);
              
              // Don't auto-close for debugging purposes
              setStatus('Error occurred. Window kept open for debugging.');
            }
          }
        }
      };
      


      // Attempt to validate, but with a fallback mechanism
      validateToken();
    };

    // Handle potential errors in the URL
    const handleAuthenticationError = () => {
      const urlParams = new URLSearchParams(window.location.search);
      const hash = window.location.hash.substring(1);
      const hashParams = new URLSearchParams(hash);
      
      // Check URL parameters for errors
      const urlError = urlParams.get('error');
      const urlErrorDescription = urlParams.get('error_description');
      
      // Check hash fragment for errors
      const hashError = hashParams.get('error');
      const hashErrorDescription = hashParams.get('error_description');

      const error = urlError || hashError;
      const errorDescription = urlErrorDescription || hashErrorDescription;

      if (error || errorDescription) {
        const errorMessage = errorDescription || error || 'Unknown authentication error';
        
        console.error('Authentication Error:', errorMessage);

        // Notify the opener about the error
        if (window.opener) {
          window.opener.postMessage({
            type: 'onedrive_oauth_error',
            error: errorMessage
          }, window.location.origin);

          setError(errorMessage);
          // Don't auto-close for debugging
        }
      }
    };

    // Process the callback
    handleAuthenticationError();
    processImplicitFlowCallback();
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-4">
      <div className="text-center p-6 bg-white rounded-lg shadow-md max-w-md w-full">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto mb-4"></div>
        <h1 className="text-xl font-semibold mb-4">{status}</h1>
        
        {error && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-md overflow-auto max-h-60">
            <p className="font-medium mb-1">Error</p>
            <pre className="whitespace-pre-wrap break-words text-sm">
              {error}
            </pre>
          </div>
        )}
        
        <div id="button-container" className="mt-4"></div>
        
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
};

export default OneDriveCallback;
