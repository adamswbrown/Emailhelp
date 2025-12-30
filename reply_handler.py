"""
reply_handler.py - Email Reply Functionality

Handles composing and sending email replies via AppleScript integration
with Mail.app and Outlook for Mac.

Supports:
- Quick replies with templates
- Reply and Reply All
- AppleScript integration for native mail clients
- Template library for common responses
"""

import subprocess
import re
from typing import Dict, Optional


class ReplyHandler:
    """Handle email replies via AppleScript"""
    
    # Quick reply templates
    TEMPLATES = {
        "will_review": {
            "name": "Will Review",
            "body": "Thanks for sending this. I'll review and get back to you shortly."
        },
        "need_info": {
            "name": "Need More Info",
            "body": "Thanks for reaching out. Could you provide more details about:\n\n[Please specify what you need]\n\nThis will help me assist you better."
        },
        "following_up": {
            "name": "Following Up",
            "body": "Following up on this - have you had a chance to review?\n\nLet me know if you need any additional information."
        },
        "thanks": {
            "name": "Thanks",
            "body": "Thanks for letting me know. Noted."
        },
        "meeting": {
            "name": "Schedule Meeting",
            "body": "Thanks for reaching out. Let's set up a meeting to discuss this.\n\nWhen works best for you this week?"
        },
        "acknowledged": {
            "name": "Acknowledged",
            "body": "I've received your message and will get back to you soon."
        }
    }
    
    def __init__(self, client='apple-mail'):
        """
        Initialize reply handler.
        
        Args:
            client: 'apple-mail' or 'outlook'
        """
        self.client = client
    
    def send_reply(
        self,
        email: Dict,
        reply_body: str,
        reply_all: bool = False
    ) -> Dict[str, any]:
        """
        Send reply via Mail.app or Outlook.
        
        Args:
            email: Email dictionary with sender, subject, etc.
            reply_body: Body text of the reply
            reply_all: Whether to reply to all recipients
        
        Returns:
            Dict with success status and message
        """
        try:
            if self.client == 'apple-mail':
                return self._send_via_mail(email, reply_body, reply_all)
            elif self.client == 'outlook':
                return self._send_via_outlook(email, reply_body, reply_all)
            else:
                return {
                    "success": False,
                    "message": f"Unknown email client: {self.client}"
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to send reply: {str(e)}"
            }
    
    def open_reply_window(
        self,
        email: Dict,
        reply_body: str = "",
        reply_all: bool = False
    ) -> Dict[str, any]:
        """
        Open reply window in Mail.app/Outlook with pre-filled content.
        
        User can edit before sending.
        
        Args:
            email: Email dictionary
            reply_body: Pre-filled body text (optional)
            reply_all: Whether to reply to all
        
        Returns:
            Dict with success status
        """
        try:
            if self.client == 'apple-mail':
                return self._open_mail_reply_window(email, reply_body, reply_all)
            else:
                return self._open_outlook_reply_window(email, reply_body, reply_all)
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to open reply window: {str(e)}"
            }
    
    def _send_via_mail(
        self,
        email: Dict,
        reply_body: str,
        reply_all: bool
    ) -> Dict[str, any]:
        """Send reply directly via Apple Mail (background)."""
        
        # Escape quotes and special characters
        reply_body = self._escape_applescript_string(reply_body)
        subject = self._escape_applescript_string(email.get('subject', ''))
        sender = email.get('sender', '').strip()
        
        # Build recipient script
        recipients_script = f'make new to recipient at end of to recipients with properties {{address:"{sender}"}}'
        
        # Add CC recipients if reply all
        if reply_all and email.get('cc'):
            cc_addresses = [addr.strip() for addr in email.get('cc', '').split(',')]
            for cc_addr in cc_addresses:
                if cc_addr:
                    cc_addr = self._escape_applescript_string(cc_addr)
                    recipients_script += f'\n            make new cc recipient at end of cc recipients with properties {{address:"{cc_addr}"}}'
        
        script = f'''
        tell application "Mail"
            set theReply to make new outgoing message with properties {{subject:"Re: {subject}", content:"{reply_body}", visible:false}}
            tell theReply
                {recipients_script}
            end tell
            send theReply
        end tell
        '''
        
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            return {
                "success": True,
                "message": "Reply sent successfully via Mail.app"
            }
        else:
            return {
                "success": False,
                "message": f"AppleScript error: {result.stderr}"
            }
    
    def _open_mail_reply_window(
        self,
        email: Dict,
        reply_body: str,
        reply_all: bool
    ) -> Dict[str, any]:
        """Open reply window in Mail.app with pre-filled content."""
        
        reply_body = self._escape_applescript_string(reply_body)
        subject = self._escape_applescript_string(email.get('subject', ''))
        sender = email.get('sender', '').strip()
        
        recipients_script = f'make new to recipient at end of to recipients with properties {{address:"{sender}"}}'
        
        if reply_all and email.get('cc'):
            cc_addresses = [addr.strip() for addr in email.get('cc', '').split(',')]
            for cc_addr in cc_addresses:
                if cc_addr:
                    cc_addr = self._escape_applescript_string(cc_addr)
                    recipients_script += f'\n            make new cc recipient at end of cc recipients with properties {{address:"{cc_addr}"}}'
        
        script = f'''
        tell application "Mail"
            activate
            set theReply to make new outgoing message with properties {{subject:"Re: {subject}", content:"{reply_body}", visible:true}}
            tell theReply
                {recipients_script}
            end tell
        end tell
        '''
        
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            return {
                "success": True,
                "message": "Reply window opened in Mail.app"
            }
        else:
            return {
                "success": False,
                "message": f"Failed to open reply window: {result.stderr}"
            }
    
    def _send_via_outlook(
        self,
        email: Dict,
        reply_body: str,
        reply_all: bool
    ) -> Dict[str, any]:
        """Send reply via Outlook using mailto: URL."""
        
        import urllib.parse
        
        subject = f"Re: {email.get('subject', '')}"
        to = email.get('sender', '')
        
        # Outlook has limited AppleScript support
        # Use mailto: URL as fallback
        subject_encoded = urllib.parse.quote(subject)
        body_encoded = urllib.parse.quote(reply_body)
        to_encoded = urllib.parse.quote(to)
        
        mailto_url = f"mailto:{to_encoded}?subject={subject_encoded}&body={body_encoded}"
        
        # Open in Outlook
        result = subprocess.run(
            ['open', '-a', 'Microsoft Outlook', mailto_url],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            return {
                "success": True,
                "message": "Reply window opened in Outlook"
            }
        else:
            return {
                "success": False,
                "message": f"Failed to open Outlook: {result.stderr}"
            }
    
    def _open_outlook_reply_window(
        self,
        email: Dict,
        reply_body: str,
        reply_all: bool
    ) -> Dict[str, any]:
        """Open reply window in Outlook."""
        return self._send_via_outlook(email, reply_body, reply_all)
    
    def _escape_applescript_string(self, text: str) -> str:
        """
        Escape string for AppleScript.
        
        Args:
            text: String to escape
        
        Returns:
            Escaped string safe for AppleScript
        """
        if not text:
            return ""
        
        # Escape quotes
        text = text.replace('\\', '\\\\')
        text = text.replace('"', '\\"')
        text = text.replace('\n', '\\n')
        text = text.replace('\r', '\\r')
        
        return text
    
    def get_templates(self) -> Dict[str, Dict[str, str]]:
        """
        Get available quick reply templates.
        
        Returns:
            Dict of template_id -> {name, body}
        """
        return self.TEMPLATES
    
    def get_template_body(self, template_id: str) -> Optional[str]:
        """
        Get body text for a specific template.
        
        Args:
            template_id: ID of the template
        
        Returns:
            Template body text or None if not found
        """
        template = self.TEMPLATES.get(template_id)
        return template['body'] if template else None
