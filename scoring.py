"""
scoring.py - Weighted Signal Scoring (WSS)

DESIGN PRINCIPLE:
Each email is scored 0-100 using explicit, deterministic signals.
All scoring logic is transparent and explainable.

SIGNAL CATEGORIES:
1. Sender Signals - Who sent the email
2. Subject Signals - What the subject line contains
3. Content Signals - What the body preview contains

SCORING PHILOSOPHY:
- Positive signals indicate actionable/important messages
- Negative signals indicate bulk/automated messages
- Neutral signals contribute nothing

ALL BEHAVIOR IS DETERMINISTIC AND LOGGED.
"""

import re
from typing import Dict, List, Tuple, Optional


class EmailScorer:
    """Calculate weighted signal scores for emails."""
    
    # Trusted domains that indicate legitimate correspondence
    TRUSTED_DOMAINS = [
        'gmail.com',
        'outlook.com',
        'hotmail.com',
        'yahoo.com',
        'icloud.com',
        'me.com',
        'mac.com',
        'altra.cloud',
        'microsoft.com',
        '2bcloud.io',
    
    ]
    
    # Bulk/automated sender patterns
    BULK_PATTERNS = [
        'noreply',
        'no-reply',
        'donotreply',
        'do-not-reply',
        'notifications',
        'automated',
        'newsletter',
        'marketing',
        'promo',
        'bounce',
    ]
    
    # Action-indicating phrases in content
    ACTION_PHRASES = [
        'can you',
        'could you',
        'please advise',
        'please review',
        'please confirm',
        'need your',
        'waiting for',
        'urgent',
        'asap',
        'action required',
        'please respond',
        'feedback needed',
        'please let me know',
        'when can you',
        'do you have',
        'can we',
        'meeting request',
        'schedule',
        'deadline',
        'follow up',
        'follow-up',
    ]
    
    # Newsletter/digest indicators in subject
    NEWSLETTER_PATTERNS = [
        'newsletter',
        'digest',
        'weekly update',
        'daily update',
        'monthly update',
        'roundup',
        'recap',
        'your daily',
        'your weekly',
        'summary',
        'automated',
        'system notification',
    ]
    
    # Unsubscribe indicators (strong signal of bulk email)
    UNSUBSCRIBE_PATTERNS = [
        'unsubscribe',
        'opt out',
        'opt-out',
        'manage preferences',
        'manage subscription',
    ]
    
    def __init__(self, user_name: Optional[str] = None, trusted_domains: Optional[List[str]] = None):
        """
        Initialize scorer with optional customization.
        
        Args:
            user_name: User's name to detect personal mentions
            trusted_domains: Additional trusted domains beyond defaults
        """
        self.user_name = user_name
        
        if trusted_domains:
            self.trusted_domains = self.TRUSTED_DOMAINS + trusted_domains
        else:
            self.trusted_domains = self.TRUSTED_DOMAINS
    
    def score_email(
        self,
        sender: str,
        subject: str,
        preview: Optional[str] = None
    ) -> Tuple[int, Dict[str, int]]:
        """
        Calculate weighted signal score for an email.
        
        Args:
            sender: Sender email address
            subject: Email subject line
            preview: Optional body preview text
        
        Returns:
            Tuple of (total_score, signal_breakdown)
            - total_score: Integer 0-100
            - signal_breakdown: Dict mapping signal name to points contributed
        """
        signals = {}
        
        # Sender signals
        sender_score = self._score_sender(sender, signals)
        
        # Subject signals
        subject_score = self._score_subject(subject, signals)
        
        # Content signals
        content_score = 0
        if preview:
            content_score = self._score_content(preview, signals)
        
        # Calculate total (clamp to 0-100)
        total = sender_score + subject_score + content_score
        total = max(0, min(100, total))
        
        return total, signals
    
    def _score_sender(self, sender: str, signals: Dict[str, int]) -> int:
        """
        Score based on sender characteristics.
        
        Signals:
        - Direct sender (not noreply): +20
        - Trusted domain: +10
        - Bulk/noreply domain: -30
        
        Args:
            sender: Sender email address
            signals: Dict to populate with signal breakdown
        
        Returns:
            Sender score contribution
        """
        score = 0
        sender_lower = sender.lower()
        
        # Extract domain
        domain = None
        if '@' in sender:
            domain = sender.split('@')[1].strip().lower()
        
        # Check for bulk/noreply patterns (negative signal)
        is_bulk = False
        for pattern in self.BULK_PATTERNS:
            if pattern in sender_lower:
                signals['bulk_sender'] = -30
                score -= 30
                is_bulk = True
                break
        
        # If not bulk, check for direct sender
        if not is_bulk:
            signals['direct_sender'] = 20
            score += 20
        
        # Check for trusted domain (positive signal)
        if domain and domain in self.trusted_domains:
            signals['trusted_domain'] = 10
            score += 10
        
        return score
    
    def _score_subject(self, subject: str, signals: Dict[str, int]) -> int:
        """
        Score based on subject line content.
        
        Signals:
        - Contains '?': +15 (question, likely needs response)
        - Starts with 'RE:': +10 (part of conversation)
        - Contains newsletter/digest: -20 (bulk content)
        
        Args:
            subject: Email subject line
            signals: Dict to populate with signal breakdown
        
        Returns:
            Subject score contribution
        """
        score = 0
        subject_lower = subject.lower()
        
        # Question mark indicates query/action needed
        if '?' in subject:
            signals['contains_question'] = 15
            score += 15
        
        # Reply indicates ongoing conversation
        if subject.startswith('RE:') or subject.startswith('Re:'):
            signals['is_reply'] = 10
            score += 10
        
        # Newsletter/digest patterns (negative)
        for pattern in self.NEWSLETTER_PATTERNS:
            if pattern in subject_lower:
                signals['newsletter_subject'] = -20
                score -= 20
                break
        
        return score
    
    def _score_content(self, preview: str, signals: Dict[str, int]) -> int:
        """
        Score based on body preview content.
        
        Signals:
        - Contains action phrases: +20
        - Mentions user name: +15
        - Contains 'unsubscribe': -40 (strong bulk indicator)
        
        Args:
            preview: Body preview text
            signals: Dict to populate with signal breakdown
        
        Returns:
            Content score contribution
        """
        score = 0
        preview_lower = preview.lower()
        
        # Check for action-indicating phrases
        for phrase in self.ACTION_PHRASES:
            if phrase in preview_lower:
                signals['action_phrase'] = 20
                score += 20
                break  # Only count once
        
        # Check for user name mention
        if self.user_name and self.user_name.lower() in preview_lower:
            signals['mentions_name'] = 15
            score += 15
        
        # Check for unsubscribe (strong bulk indicator)
        for pattern in self.UNSUBSCRIBE_PATTERNS:
            if pattern in preview_lower:
                signals['has_unsubscribe'] = -40
                score -= 40
                break
        
        return score
    
    def explain_score(self, signals: Dict[str, int]) -> str:
        """
        Generate human-readable explanation of score.
        
        Args:
            signals: Signal breakdown dict from score_email()
        
        Returns:
            Multi-line explanation string
        """
        lines = []
        
        for signal_name, points in sorted(signals.items(), key=lambda x: -abs(x[1])):
            sign = '+' if points >= 0 else ''
            lines.append(f"  {signal_name}: {sign}{points}")
        
        return '\n'.join(lines)
