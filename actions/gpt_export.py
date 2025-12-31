"""
gpt_export.py - Export Email Context to GPT

Formats email content for pasting into ChatGPT, including:
- Email metadata (sender, subject, date)
- Classification and scoring details
- Full email content
- Signal breakdown for context
"""

import subprocess
from typing import Dict
from datetime import datetime


class GPTExporter:
    """Export email context for ChatGPT analysis."""
    
    @staticmethod
    def format_for_gpt(email: Dict, include_signals: bool = True) -> str:
        """
        Format email for ChatGPT prompt.
        
        Args:
            email: Email dictionary with all metadata
            include_signals: Whether to include signal breakdown
        
        Returns:
            Formatted text ready to paste into ChatGPT
        """
        # Format date
        if isinstance(email.get('date'), (int, float)):
            date_obj = datetime.fromtimestamp(email['date'])
            date_str = date_obj.strftime('%d/%m/%Y %H:%M')
        else:
            date_str = str(email.get('date', 'Unknown'))
        
        # Build context
        context = f"""I received this email:

From: {email.get('sender', 'Unknown')}
To: Me
Date: {date_str}
Subject: {email.get('subject', 'No subject')}

Classification: {email.get('category', 'Unknown')} (Score: {email.get('score', 0)})
"""
        
        # Add signal breakdown if requested
        if include_signals and email.get('signals'):
            context += "\nScoring Signals:\n"
            for signal, points in sorted(email['signals'].items(), key=lambda x: -abs(x[1])):
                sign = '+' if points >= 0 else ''
                context += f"  • {signal}: {sign}{points}\n"
        
        # Add email content
        context += f"\n---\n\n{email.get('content', email.get('preview', 'No content available'))}\n\n---\n\n"
        
        # Add prompt
        context += "Please help me:\n"
        
        return context
    
    @staticmethod
    def format_for_gpt_draft_reply(email: Dict) -> str:
        """
        Format email for asking GPT to draft a reply.
        
        Args:
            email: Email dictionary
        
        Returns:
            Formatted prompt for GPT to draft reply
        """
        context = GPTExporter.format_for_gpt(email, include_signals=False)
        
        # Replace generic prompt with draft request
        context = context.replace(
            "Please help me:",
            """Please draft a professional reply to this email that:
- Acknowledges the key points
- Provides a clear response or next steps
- Maintains a professional tone
- Is concise but complete

Draft reply:"""
        )
        
        return context
    
    @staticmethod
    def copy_to_clipboard(text: str) -> bool:
        """
        Copy text to macOS clipboard.
        
        Args:
            text: Text to copy
        
        Returns:
            True if successful, False otherwise
        """
        try:
            process = subprocess.Popen(
                'pbcopy',
                env={'LANG': 'en_US.UTF-8'},
                stdin=subprocess.PIPE
            )
            process.communicate(text.encode('utf-8'))
            return process.returncode == 0
        except Exception as e:
            print(f"Failed to copy to clipboard: {e}")
            return False
    
    @staticmethod
    def export_for_analysis(email: Dict) -> str:
        """
        Export with analysis request.
        
        Args:
            email: Email dictionary
        
        Returns:
            Formatted text
        """
        return GPTExporter.format_for_gpt(email, include_signals=True)
    
    @staticmethod
    def export_for_draft_reply(email: Dict) -> str:
        """
        Export with draft reply request.
        
        Args:
            email: Email dictionary
        
        Returns:
            Formatted text
        """
        return GPTExporter.format_for_gpt_draft_reply(email)
