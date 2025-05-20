import logging
import json
import base64
from typing import Dict, Any, Optional, List, Union
import aiohttp
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.services.email_auth_manager import email_auth_manager

logger = logging.getLogger(__name__)

class AgentEmailService:
    """Email service for agent-based email operations using user OAuth tokens"""
    
    @staticmethod
    async def list_messages(
        provider: str, 
        user_id: str, 
        folder: str = "inbox", 
        max_results: int = 10,
        query: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List messages from a specific folder or matching a search query.
        
        Args:
            provider: The email provider
            user_id: The user ID
            folder: The folder to list messages from
            max_results: Maximum number of messages to return
            query: Optional search query
            
        Returns:
            List of message metadata
        """
        # Verify authentication
        if not email_auth_manager.is_authenticated(provider, user_id):
            raise ValueError("Not authenticated")
            
        # Refresh token if needed
        await email_auth_manager.refresh_token_if_needed(provider, user_id)
        
        # Get session data
        session_data = email_auth_manager.get_session_data(provider, user_id)
        
        # Provider-specific implementations
        if provider.lower() == "gmail":
            return await AgentEmailService._list_gmail_messages(
                session_data, folder, max_results, query
            )
        elif provider.lower() == "outlook":
            return await AgentEmailService._list_outlook_messages(
                session_data, folder, max_results, query
            )
        else:
            raise ValueError(f"Unsupported provider: {provider}")
            
    @staticmethod
    async def _list_gmail_messages(
        session_data: Dict[str, Any],
        folder: str = "inbox",
        max_results: int = 10,
        query: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List messages from Gmail"""
        
        # Map folder names to Gmail labels
        folder_mapping = {
            "inbox": "INBOX",
            "sent": "SENT",
            "drafts": "DRAFTS",
            "trash": "TRASH",
            "spam": "SPAM"
        }
        
        # Build query parameters
        params = {
            "maxResults": str(max_results)
        }
        
        # Add label filter
        gmail_label = folder_mapping.get(folder.lower(), "INBOX")
        
        # Build Gmail query
        q_parts = [f"label:{gmail_label}"]
        
        # Add search query if provided
        if query:
            q_parts.append(query)
            
        params["q"] = " ".join(q_parts)
        
        # Call Gmail API
        base_url = "https://www.googleapis.com/gmail/v1/users/me/messages"
        headers = {
            "Authorization": f"Bearer {session_data['access_token']}"
        }
        
        # Get message IDs
        async with aiohttp.ClientSession() as session:
            async with session.get(base_url, params=params, headers=headers) as response:
                if response.status != 200:
                    logger.error(f"Failed to list Gmail messages: {response.status}")
                    return []
                    
                data = await response.json()
                messages = data.get("messages", [])
                
        # Get message details (in batches to avoid rate limits)
        batch_size = 5
        result = []
        
        for i in range(0, len(messages), batch_size):
            batch = messages[i:i+batch_size]
            
            for msg in batch:
                msg_id = msg["id"]
                msg_url = f"{base_url}/{msg_id}"
                
                # Get message details
                async with aiohttp.ClientSession() as session:
                    async with session.get(msg_url, headers=headers) as response:
                        if response.status != 200:
                            logger.error(f"Failed to get Gmail message {msg_id}: {response.status}")
                            continue
                            
                        msg_data = await response.json()
                        
                        # Extract headers
                        headers_dict = {}
                        for header in msg_data.get("payload", {}).get("headers", []):
                            headers_dict[header["name"].lower()] = header["value"]
                            
                        # Extract snippet
                        snippet = msg_data.get("snippet", "")
                        
                        # Create result entry
                        result.append({
                            "id": msg_id,
                            "thread_id": msg_data.get("threadId"),
                            "label_ids": msg_data.get("labelIds", []),
                            "snippet": snippet,
                            "size_estimate": msg_data.get("sizeEstimate", 0),
                            "history_id": msg_data.get("historyId"),
                            "internal_date": msg_data.get("internalDate"),
                            
                            # Extracted headers
                            "from": headers_dict.get("from", ""),
                            "to": headers_dict.get("to", ""),
                            "subject": headers_dict.get("subject", ""),
                            "date": headers_dict.get("date", ""),
                            "cc": headers_dict.get("cc", ""),
                            "bcc": headers_dict.get("bcc", ""),
                            
                            # Metadata
                            "folder": folder,
                            "provider": "gmail",
                            "is_unread": "UNREAD" in msg_data.get("labelIds", [])
                        })
        
        return result
        
    @staticmethod
    async def _list_outlook_messages(
        session_data: Dict[str, Any],
        folder: str = "inbox",
        max_results: int = 10,
        query: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List messages from Outlook"""
        
        # Build Microsoft Graph API request
        base_url = "https://graph.microsoft.com/v1.0/me/messages"
        
        # Parameters
        params = {
            "$top": str(max_results),
            "$orderby": "receivedDateTime desc"
        }
        
        # Add folder filter
        if folder.lower() != "inbox":
            if folder.lower() == "sent":
                base_url = "https://graph.microsoft.com/v1.0/me/mailFolders/sentitems/messages"
            elif folder.lower() == "drafts":
                base_url = "https://graph.microsoft.com/v1.0/me/mailFolders/drafts/messages"
            elif folder.lower() == "deleted":
                base_url = "https://graph.microsoft.com/v1.0/me/mailFolders/deleteditems/messages"
            elif folder.lower() == "junk":
                base_url = "https://graph.microsoft.com/v1.0/me/mailFolders/junkemail/messages"
        
        # Add search query if provided
        if query:
            params["$search"] = f'"{query}"'
            
        # Set up headers
        headers = {
            "Authorization": f"Bearer {session_data['access_token']}",
            "Accept": "application/json"
        }
        
        # Make API request
        async with aiohttp.ClientSession() as session:
            async with session.get(base_url, params=params, headers=headers) as response:
                if response.status != 200:
                    logger.error(f"Failed to list Outlook messages: {response.status}")
                    return []
                    
                data = await response.json()
                messages = data.get("value", [])
                
        # Transform to standard format
        result = []
        for msg in messages:
            result.append({
                "id": msg.get("id"),
                "internet_message_id": msg.get("internetMessageId"),
                "subject": msg.get("subject", ""),
                "from": msg.get("from", {}).get("emailAddress", {}).get("address", ""),
                "from_name": msg.get("from", {}).get("emailAddress", {}).get("name", ""),
                "to": ", ".join([r.get("emailAddress", {}).get("address", "") for r in msg.get("toRecipients", [])]),
                "to_recipients": msg.get("toRecipients", []),
                "cc": ", ".join([r.get("emailAddress", {}).get("address", "") for r in msg.get("ccRecipients", [])]),
                "cc_recipients": msg.get("ccRecipients", []),
                "bcc": ", ".join([r.get("emailAddress", {}).get("address", "") for r in msg.get("bccRecipients", [])]),
                "bcc_recipients": msg.get("bccRecipients", []),
                "body_preview": msg.get("bodyPreview", ""),
                "is_read": msg.get("isRead", False),
                "received_date": msg.get("receivedDateTime", ""),
                "sent_date": msg.get("sentDateTime", ""),
                "has_attachments": msg.get("hasAttachments", False),
                "importance": msg.get("importance", "normal"),
                
                # Metadata
                "folder": folder,
                "provider": "outlook",
                "is_unread": not msg.get("isRead", False)
            })
            
        return result

    @staticmethod
    async def get_message(
        provider: str,
        user_id: str,
        message_id: str,
        format: str = "full"
    ) -> Dict[str, Any]:
        """
        Get a specific message by ID.
        
        Args:
            provider: The email provider
            user_id: The user ID
            message_id: The message ID
            format: The format to return the message in (full, minimal, etc.)
            
        Returns:
            Message data
        """
        # Verify authentication
        if not email_auth_manager.is_authenticated(provider, user_id):
            raise ValueError("Not authenticated")
            
        # Refresh token if needed
        await email_auth_manager.refresh_token_if_needed(provider, user_id)
        
        # Get session data
        session_data = email_auth_manager.get_session_data(provider, user_id)
        
        # Provider-specific implementations
        if provider.lower() == "gmail":
            return await AgentEmailService._get_gmail_message(session_data, message_id, format)
        elif provider.lower() == "outlook":
            return await AgentEmailService._get_outlook_message(session_data, message_id, format)
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    @staticmethod
    async def _get_gmail_message(
        session_data: Dict[str, Any],
        message_id: str,
        format: str = "full"
    ) -> Dict[str, Any]:
        """Get a specific Gmail message"""
        
        # Build Gmail API request
        url = f"https://www.googleapis.com/gmail/v1/users/me/messages/{message_id}"
        
        # Add format parameter if specified
        params = {}
        if format.lower() == "minimal":
            params["format"] = "minimal"
        elif format.lower() == "metadata":
            params["format"] = "metadata"
        else:
            params["format"] = "full"
            
        # Set up headers
        headers = {
            "Authorization": f"Bearer {session_data['access_token']}"
        }
        
        # Make API request
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers) as response:
                if response.status != 200:
                    logger.error(f"Failed to get Gmail message {message_id}: {response.status}")
                    return {}
                    
                data = await response.json()
                
        # Extract headers
        headers_dict = {}
        for header in data.get("payload", {}).get("headers", []):
            headers_dict[header["name"].lower()] = header["value"]
            
        # Extract body
        body = ""
        bodyHtml = ""
        
        # Process parts to find body content
        def extract_body(part):
            nonlocal body, bodyHtml
            
            if "body" in part and "data" in part["body"]:
                # Decode body data
                data = part["body"]["data"]
                decoded_data = base64.urlsafe_b64decode(data).decode("utf-8")
                
                if part["mimeType"] == "text/plain":
                    body = decoded_data
                elif part["mimeType"] == "text/html":
                    bodyHtml = decoded_data
            
            # Process nested parts
            if "parts" in part:
                for nested_part in part["parts"]:
                    extract_body(nested_part)
        
        # Start extraction with payload
        if "payload" in data:
            extract_body(data["payload"])
            
        # Build result
        result = {
            "id": data.get("id"),
            "thread_id": data.get("threadId"),
            "label_ids": data.get("labelIds", []),
            "snippet": data.get("snippet", ""),
            
            # Extracted headers
            "from": headers_dict.get("from", ""),
            "to": headers_dict.get("to", ""),
            "subject": headers_dict.get("subject", ""),
            "date": headers_dict.get("date", ""),
            "cc": headers_dict.get("cc", ""),
            "bcc": headers_dict.get("bcc", ""),
            
            # Body content
            "body": body,
            "body_html": bodyHtml,
            
            # Metadata
            "provider": "gmail",
            "is_unread": "UNREAD" in data.get("labelIds", [])
        }
        
        return result
        
    @staticmethod
    async def _get_outlook_message(
        session_data: Dict[str, Any],
        message_id: str,
        format: str = "full"
    ) -> Dict[str, Any]:
        """Get a specific Outlook message"""
        
        # Build Microsoft Graph API request
        url = f"https://graph.microsoft.com/v1.0/me/messages/{message_id}"
        
        # Add parameters if needed
        params = {}
        if format.lower() == "minimal":
            params["$select"] = "id,subject,from,toRecipients,receivedDateTime,isRead"
            
        # Set up headers
        headers = {
            "Authorization": f"Bearer {session_data['access_token']}",
            "Accept": "application/json"
        }
        
        # Make API request
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers) as response:
                if response.status != 200:
                    logger.error(f"Failed to get Outlook message {message_id}: {response.status}")
                    return {}
                    
                data = await response.json()
                
        # Transform to standard format
        result = {
            "id": data.get("id"),
            "internet_message_id": data.get("internetMessageId"),
            "subject": data.get("subject", ""),
            "from": data.get("from", {}).get("emailAddress", {}).get("address", ""),
            "from_name": data.get("from", {}).get("emailAddress", {}).get("name", ""),
            "to": ", ".join([r.get("emailAddress", {}).get("address", "") for r in data.get("toRecipients", [])]),
            "to_recipients": data.get("toRecipients", []),
            "cc": ", ".join([r.get("emailAddress", {}).get("address", "") for r in data.get("ccRecipients", [])]),
            "cc_recipients": data.get("ccRecipients", []),
            "bcc": ", ".join([r.get("emailAddress", {}).get("address", "") for r in data.get("bccRecipients", [])]),
            "bcc_recipients": data.get("bccRecipients", []),
            
            # Body content
            "body_preview": data.get("bodyPreview", ""),
            "body": data.get("body", {}).get("content", ""),
            "body_content_type": data.get("body", {}).get("contentType", "text"),
            
            # Metadata
            "is_read": data.get("isRead", False),
            "received_date": data.get("receivedDateTime", ""),
            "sent_date": data.get("sentDateTime", ""),
            "has_attachments": data.get("hasAttachments", False),
            "importance": data.get("importance", "normal"),
            "provider": "outlook",
            "is_unread": not data.get("isRead", False)
        }
        
        return result

    @staticmethod
    async def send_message(
        provider: str,
        user_id: str,
        to: str,
        subject: str,
        body: str,
        body_type: str = "html",
        cc: Optional[str] = None,
        bcc: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send an email message.
        
        Args:
            provider: The email provider
            user_id: The user ID
            to: Recipient email address(es)
            subject: Email subject
            body: Email body content
            body_type: Body content type (html or text)
            cc: Optional CC recipients
            bcc: Optional BCC recipients
            
        Returns:
            Status of the send operation
        """
        # Verify authentication
        if not email_auth_manager.is_authenticated(provider, user_id):
            raise ValueError("Not authenticated")
            
        # Refresh token if needed
        await email_auth_manager.refresh_token_if_needed(provider, user_id)
        
        # Get session data
        session_data = email_auth_manager.get_session_data(provider, user_id)
        
        # Provider-specific implementations
        if provider.lower() == "gmail":
            return await AgentEmailService._send_gmail_message(
                session_data, to, subject, body, body_type, cc, bcc
            )
        elif provider.lower() == "outlook":
            return await AgentEmailService._send_outlook_message(
                session_data, to, subject, body, body_type, cc, bcc
            )
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    @staticmethod
    async def _send_gmail_message(
        session_data: Dict[str, Any],
        to: str,
        subject: str,
        body: str,
        body_type: str = "html",
        cc: Optional[str] = None,
        bcc: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send an email using Gmail API"""
        
        # Create message
        message = MIMEMultipart()
        message["to"] = to
        message["subject"] = subject
        
        if cc:
            message["cc"] = cc
        if bcc:
            message["bcc"] = bcc
            
        # Set From header if available
        user_email = session_data.get("user_email", "me")
        message["from"] = user_email
        
        # Add body based on type
        if body_type.lower() == "html":
            message.attach(MIMEText(body, "html"))
        else:
            message.attach(MIMEText(body, "plain"))
            
        # Encode message
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        # Prepare API request
        url = "https://www.googleapis.com/gmail/v1/users/me/messages/send"
        headers = {
            "Authorization": f"Bearer {session_data['access_token']}",
            "Content-Type": "application/json"
        }
        
        data = {
            "raw": encoded_message
        }
        
        # Send message
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Failed to send Gmail message: {response.status} - {error_text}")
                    return {
                        "status": "error",
                        "error": f"Failed to send message: {response.status}",
                        "details": error_text
                    }
                    
                result = await response.json()
                
        return {
            "status": "success",
            "message_id": result.get("id"),
            "thread_id": result.get("threadId"),
            "provider": "gmail"
        }
        
    @staticmethod
    async def _send_outlook_message(
        session_data: Dict[str, Any],
        to: str,
        subject: str,
        body: str,
        body_type: str = "html",
        cc: Optional[str] = None,
        bcc: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send an email using Microsoft Graph API"""
        
        # Prepare recipients
        to_recipients = []
        for email in to.split(","):
            email = email.strip()
            if email:
                to_recipients.append({
                    "emailAddress": {
                        "address": email
                    }
                })
                
        # Prepare CC recipients
        cc_recipients = []
        if cc:
            for email in cc.split(","):
                email = email.strip()
                if email:
                    cc_recipients.append({
                        "emailAddress": {
                            "address": email
                        }
                    })
                    
        # Prepare BCC recipients
        bcc_recipients = []
        if bcc:
            for email in bcc.split(","):
                email = email.strip()
                if email:
                    bcc_recipients.append({
                        "emailAddress": {
                            "address": email
                        }
                    })
        
        # Prepare message
        message_data = {
            "subject": subject,
            "body": {
                "contentType": "HTML" if body_type.lower() == "html" else "Text",
                "content": body
            },
            "toRecipients": to_recipients,
            "ccRecipients": cc_recipients,
            "bccRecipients": bcc_recipients
        }
        
        # Send message
        url = "https://graph.microsoft.com/v1.0/me/sendMail"
        headers = {
            "Authorization": f"Bearer {session_data['access_token']}",
            "Content-Type": "application/json"
        }
        
        data = {
            "message": message_data,
            "saveToSentItems": "true"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as response:
                if response.status != 202:  # Outlook returns 202 Accepted
                    error_text = await response.text()
                    logger.error(f"Failed to send Outlook message: {response.status} - {error_text}")
                    return {
                        "status": "error",
                        "error": f"Failed to send message: {response.status}",
                        "details": error_text
                    }
        
        return {
            "status": "success",
            "provider": "outlook"
        }

    @staticmethod
    async def search_messages(
        provider: str,
        user_id: str,
        query: str,
        max_results: int = 10,
        folder: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for messages matching a query.
        
        Args:
            provider: The email provider
            user_id: The user ID
            query: The search query
            max_results: Maximum number of results to return
            folder: Optional folder to search in
            
        Returns:
            List of message metadata
        """
        # For Gmail and Outlook, we can use the list_messages function with a query
        return await AgentEmailService.list_messages(
            provider=provider,
            user_id=user_id,
            folder=folder or "inbox",
            max_results=max_results,
            query=query
        )

# Create singleton instance
agent_email_service = AgentEmailService()
