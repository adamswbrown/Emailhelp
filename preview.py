"""
preview.py - Lightweight Email Body Preview Extraction

EMLX FORMAT:
Apple Mail stores individual messages in .emlx files. Each file contains:
- First line: byte count (metadata)
- Remaining lines: RFC 822 email message
- Optional XML plist at the end

APPROACH:
- Parse only the first ~300 characters of body text
- Strip signatures, quoted replies, and HTML
- Ignore attachments entirely
- Fail gracefully if file is missing or malformed

PERFORMANCE:
- Read minimal bytes from disk
- Use simple heuristics rather than full email parsing
"""

import re
import email
from email import policy
from pathlib import Path
from typing import Optional
import html


class EmailPreview:
    """Extract lightweight preview text from .emlx files."""
    
    # Common signature markers
    SIGNATURE_MARKERS = [
        '--',  # Standard signature delimiter
        '-- ',
        '___',
        'Sent from',
        'Get Outlook for',
    ]
    
    # Quote markers
    QUOTE_MARKERS = [
        'On .* wrote:',  # "On Jan 1, 2025, John wrote:"
        'From:.*Sent:',  # Outlook-style quote header
        '>',  # Quoted line prefix
        '________________________________',  # Outlook divider
    ]
    
    # Maximum characters to extract
    MAX_PREVIEW_LENGTH = 300
    
    @staticmethod
    def extract_from_emlx(emlx_path: str) -> Optional[str]:
        """
        Extract preview text from an .emlx file.
        
        Args:
            emlx_path: Path to the .emlx file
        
        Returns:
            Preview text (up to ~300 chars) or None if extraction fails
        """
        if not emlx_path or not Path(emlx_path).exists():
            return None
        
        try:
            with open(emlx_path, 'rb') as f:
                # First line is byte count - skip it
                first_line = f.readline()
                
                # Read the rest as email message
                # For performance, limit read to ~10KB (enough for preview)
                raw_email = f.read(10240)
            
            # Parse email message
            msg = email.message_from_bytes(raw_email, policy=policy.default)
            
            # Extract body text
            body_text = EmailPreview._extract_body(msg)
            
            if not body_text:
                return None
            
            # Clean and truncate
            preview = EmailPreview._clean_body(body_text)
            return preview
            
        except Exception as e:
            # Fail gracefully - preview is optional
            return None
    
    @staticmethod
    def _extract_body(msg) -> Optional[str]:
        """
        Extract plain text body from email message.
        
        Args:
            msg: email.message.Message object
        
        Returns:
            Body text or None
        """
        body = None
        
        # Try to get plain text body
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                
                # Prefer text/plain
                if content_type == 'text/plain':
                    try:
                        body = part.get_content()
                        break
                    except:
                        continue
                
                # Fall back to text/html
                elif content_type == 'text/html' and body is None:
                    try:
                        html_content = part.get_content()
                        body = EmailPreview._strip_html(html_content)
                    except:
                        continue
        else:
            # Not multipart - get content directly
            content_type = msg.get_content_type()
            try:
                if content_type == 'text/plain':
                    body = msg.get_content()
                elif content_type == 'text/html':
                    html_content = msg.get_content()
                    body = EmailPreview._strip_html(html_content)
            except:
                pass
        
        return body
    
    @staticmethod
    def _strip_html(html_content: str) -> str:
        """
        Strip HTML tags to get plain text.
        
        Args:
            html_content: HTML string
        
        Returns:
            Plain text
        """
        # Unescape HTML entities
        text = html.unescape(html_content)
        
        # Remove script and style elements
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    @staticmethod
    def _clean_body(body: str) -> str:
        """
        Clean body text by removing signatures and quotes, then truncate.
        
        Args:
            body: Raw body text
        
        Returns:
            Cleaned and truncated preview
        """
        lines = body.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            
            # Check for signature markers
            if any(marker in line for marker in EmailPreview.SIGNATURE_MARKERS):
                break
            
            # Check for quote markers
            is_quote = False
            for pattern in EmailPreview.QUOTE_MARKERS:
                if re.search(pattern, line, re.IGNORECASE):
                    is_quote = True
                    break
            
            if is_quote:
                break
            
            # Skip empty lines
            if not line:
                continue
            
            cleaned_lines.append(line)
            
            # Stop early if we have enough content
            current_length = sum(len(l) for l in cleaned_lines)
            if current_length >= EmailPreview.MAX_PREVIEW_LENGTH:
                break
        
        # Join and truncate
        preview = ' '.join(cleaned_lines)
        
        if len(preview) > EmailPreview.MAX_PREVIEW_LENGTH:
            preview = preview[:EmailPreview.MAX_PREVIEW_LENGTH] + '...'
        
        return preview
    
    @staticmethod
    def extract_preview_simple(subject: str, sender: str, preview_text: Optional[str]) -> str:
        """
        Create a simple preview from available metadata.
        
        Used when .emlx file is not available.
        
        Args:
            subject: Email subject
            sender: Sender address
            preview_text: Optional body preview
        
        Returns:
            Combined preview string
        """
        if preview_text:
            return preview_text
        
        # Fall back to subject
        if subject:
            return f"[Subject: {subject}]"
        
        return "[No preview available]"
