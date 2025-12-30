#!/usr/bin/env python3
"""
analyze_emails.py - Analyze email patterns to improve classification

This script analyzes your actual emails to:
1. Identify common sender domains
2. Analyze subject line patterns
3. Review score distributions
4. Analyze full email content for better rule detection
5. Suggest improvements to scoring signals and thresholds

Supports both Apple Mail and Outlook for Mac.
"""

import sys
from collections import Counter, defaultdict
from typing import List, Dict, Any, Optional

from email_reader import create_reader
from preview import EmailPreview
from scoring import EmailScorer
from classifier import EmailClassifier


def extract_full_content(msg: Dict[str, Any], reader_type: str) -> Optional[str]:
    """
    Extract full email content from message.
    
    Args:
        msg: Message dictionary
        reader_type: 'apple-mail' or 'outlook'
        
    Returns:
        Full email body text or None
    """
    # For Outlook, use the preview field (which often contains full body)
    if reader_type == 'outlook':
        preview = msg.get('preview') or msg.get('Message_Preview')
        if preview:
            return preview
    
    # For Apple Mail, try to read from .emlx file
    elif reader_type == 'apple-mail':
        emlx_path = msg.get('emlx_path')
        if emlx_path:
            # Try to extract full body from .emlx
            try:
                import email
                from email import policy
                from pathlib import Path
                
                if Path(emlx_path).exists():
                    with open(emlx_path, 'rb') as f:
                        first_line = f.readline()  # Skip byte count
                        raw_email = f.read()  # Read full email
                    
                    msg_obj = email.message_from_bytes(raw_email, policy=policy.default)
                    body = EmailPreview._extract_body(msg_obj)
                    return body
            except Exception:
                pass
    
    return None


def analyze_emails(
    limit: int = 200,
    since_days: int = None,
    client: Optional[str] = None,
    account: Optional[str] = None,
    mailbox: Optional[str] = 'Inbox'
) -> Dict[str, Any]:
    """
    Analyze email patterns and generate recommendations.
    
    Args:
        limit: Maximum number of emails to analyze
        since_days: Only analyze emails from the last N days (None = all emails)
        client: 'apple-mail', 'outlook', or None for auto-detect
        account: Filter by account email address
        
    Returns:
        Dictionary with analysis results and recommendations
    """
    if since_days:
        print(f"Analyzing emails from the last {since_days} days...\n", file=sys.stderr)
    else:
        print("Analyzing all available emails...\n", file=sys.stderr)
    
    # Create reader (supports both Apple Mail and Outlook)
    reader = create_reader(client=client)
    scorer = EmailScorer()
    
    # Detect reader type
    reader_type = 'outlook' if 'Outlook' in str(type(reader)) else 'apple-mail'
    print(f"Using {reader_type} database...\n", file=sys.stderr)
    
    with reader:
        messages = reader.query_messages(
            limit=limit,
            since_days=since_days,
            account=account,
            mailbox=mailbox
        )
    
    if not messages:
        print("No messages found to analyze.", file=sys.stderr)
        return {}
    
    print(f"Analyzing {len(messages)} emails...\n", file=sys.stderr)
    
    # Analyze patterns
    domain_counter = Counter()
    subject_patterns = defaultdict(int)
    score_distribution = defaultdict(int)
    category_distribution = defaultdict(int)
    sender_patterns = defaultdict(int)
    content_patterns = defaultdict(int)
    
    # Common patterns to track
    question_subjects = 0
    reply_subjects = 0
    newsletter_subjects = 0
    
    bulk_senders = []
    trusted_senders = []
    action_emails = []
    ignore_emails = []
    misclassified_emails = []
    
    # Track content-based patterns
    action_phrases_in_content = Counter()
    informational_phrases_in_content = Counter()
    
    for msg in messages:
        sender = msg.get('sender', '') or ''
        subject = msg.get('subject', '') or ''
        
        # Extract full content
        full_content = extract_full_content(msg, reader_type)
        content_text = (full_content or '').lower()
        
        # Extract domain
        if '@' in sender:
            domain = sender.split('@')[1].strip().lower()
            domain_counter[domain] += 1
        
        # Score the email (with content if available)
        preview_text = full_content[:500] if full_content else None  # Use first 500 chars for scoring
        score, signals = scorer.score_email(sender, subject, preview_text)
        category = EmailClassifier.classify(score)
        
        # Track distributions
        score_distribution[score] += 1
        category_distribution[category.value] += 1
        
        # Analyze subject patterns
        subject_lower = subject.lower()
        if '?' in subject:
            question_subjects += 1
        if subject.startswith('RE:') or subject.startswith('Re:'):
            reply_subjects += 1
        if any(p in subject_lower for p in ['newsletter', 'digest', 'update', 'roundup']):
            newsletter_subjects += 1
        
        # Analyze content patterns
        if content_text:
            # Look for action phrases in content
            action_keywords = ['action required', 'please respond', 'deadline', 'urgent', 
                             'meeting', 'schedule', 'call', 'follow up', 'review', 'approve']
            for keyword in action_keywords:
                if keyword in content_text:
                    action_phrases_in_content[keyword] += 1
            
            # Look for informational phrases
            info_keywords = ['for your information', 'fyi', 'notification', 'automated',
                           'system notification', 'license expiration', 'expires soon',
                           'no action required', 'informational']
            for keyword in info_keywords:
                if keyword in content_text:
                    informational_phrases_in_content[keyword] += 1
        
        # Track sender patterns
        sender_lower = sender.lower()
        if any(p in sender_lower for p in ['noreply', 'no-reply', 'donotreply']):
            bulk_senders.append((sender, subject, score))
        elif domain in scorer.trusted_domains:
            trusted_senders.append((sender, subject, score))
        
        # Track high/low scoring emails for review
        if score >= 60:
            action_emails.append((sender, subject, score, signals, full_content[:200] if full_content else None))
        elif score < 30:
            ignore_emails.append((sender, subject, score, signals, full_content[:200] if full_content else None))
        
        # Track potentially misclassified emails (high score but low content action signals)
        if score >= 50 and full_content:
            has_action_in_content = any(kw in content_text for kw in ['action required', 'please respond', 'deadline', 'urgent'])
            has_info_in_content = any(kw in content_text for kw in ['for your information', 'fyi', 'no action required', 'informational'])
            
            if not has_action_in_content and has_info_in_content:
                misclassified_emails.append({
                    'sender': sender,
                    'subject': subject,
                    'score': score,
                    'category': category.value,
                    'content_preview': full_content[:300]
                })
    
    # Generate recommendations
    recommendations = generate_recommendations(
        domain_counter,
        score_distribution,
        category_distribution,
        question_subjects,
        reply_subjects,
        newsletter_subjects,
        len(messages),
        bulk_senders,
        trusted_senders,
        action_emails,
        ignore_emails,
        action_phrases_in_content,
        informational_phrases_in_content,
        misclassified_emails
    )
    
    return {
        'total_emails': len(messages),
        'domain_counter': dict(domain_counter.most_common(20)),
        'score_distribution': dict(score_distribution),
        'category_distribution': dict(category_distribution),
        'question_subjects': question_subjects,
        'reply_subjects': reply_subjects,
        'newsletter_subjects': newsletter_subjects,
        'recommendations': recommendations,
        'bulk_senders': bulk_senders[:10],
        'trusted_senders': trusted_senders[:10],
        'action_emails': action_emails[:10],
        'ignore_emails': ignore_emails[:10],
        'misclassified_emails': misclassified_emails[:10],
        'action_phrases_in_content': dict(action_phrases_in_content.most_common(10)),
        'informational_phrases_in_content': dict(informational_phrases_in_content.most_common(10)),
    }


def generate_recommendations(
    domain_counter: Counter,
    score_distribution: Dict[int, int],
    category_distribution: Dict[str, int],
    question_subjects: int,
    reply_subjects: int,
    newsletter_subjects: int,
    total_emails: int,
    bulk_senders: List,
    trusted_senders: List,
    action_emails: List,
    ignore_emails: List,
    action_phrases_in_content: Counter,
    informational_phrases_in_content: Counter,
    misclassified_emails: List
) -> Dict[str, Any]:
    """Generate recommendations based on analysis."""
    
    recs = {
        'trusted_domains': [],
        'threshold_adjustments': {},
        'signal_adjustments': {},
        'patterns_found': {},
        'content_patterns': {},
        'new_action_phrases': [],
        'new_informational_phrases': []
    }
    
    # Find common domains that aren't in trusted list
    scorer = EmailScorer()
    top_domains = domain_counter.most_common(15)
    for domain, count in top_domains:
        if domain not in scorer.trusted_domains and count >= total_emails * 0.05:  # At least 5% of emails
            recs['trusted_domains'].append(domain)
    
    # Analyze score distribution
    scores = list(score_distribution.keys())
    if scores:
        avg_score = sum(s * count for s, count in score_distribution.items()) / sum(score_distribution.values())
        min_score = min(scores)
        max_score = max(scores)
        
        # Check if thresholds need adjustment
        action_count = category_distribution.get('ACTION', 0)
        fyi_count = category_distribution.get('FYI', 0)
        ignore_count = category_distribution.get('IGNORE', 0)
        
        action_pct = (action_count / total_emails) * 100 if total_emails > 0 else 0
        fyi_pct = (fyi_count / total_emails) * 100 if total_emails > 0 else 0
        ignore_pct = (ignore_count / total_emails) * 100 if total_emails > 0 else 0
        
        recs['patterns_found'] = {
            'average_score': round(avg_score, 1),
            'score_range': (min_score, max_score),
            'action_percentage': round(action_pct, 1),
            'fyi_percentage': round(fyi_pct, 1),
            'ignore_percentage': round(ignore_pct, 1),
        }
        
        # Suggest threshold adjustments
        if action_pct < 10:
            recs['threshold_adjustments']['ACTION'] = {
                'current': EmailClassifier.ACTION_THRESHOLD,
                'suggested': EmailClassifier.ACTION_THRESHOLD - 10,
                'reason': f'Only {action_pct:.1f}% classified as ACTION - threshold may be too high'
            }
        elif action_pct > 40:
            recs['threshold_adjustments']['ACTION'] = {
                'current': EmailClassifier.ACTION_THRESHOLD,
                'suggested': EmailClassifier.ACTION_THRESHOLD + 10,
                'reason': f'{action_pct:.1f}% classified as ACTION - threshold may be too low'
            }
    
    # Analyze content patterns
    recs['content_patterns'] = {
        'action_phrases': dict(action_phrases_in_content.most_common(10)),
        'informational_phrases': dict(informational_phrases_in_content.most_common(10)),
        'misclassified_count': len(misclassified_emails)
    }
    
    # Suggest new action phrases from content
    # Get existing phrases from scorer instance
    existing_action_phrases = [p.lower() for p in scorer.ACTION_PHRASES]
    existing_info_phrases = [p.lower() for p in scorer.INFORMATIONAL_PATTERNS]
    
    for phrase, count in action_phrases_in_content.most_common(10):
        if phrase.lower() not in existing_action_phrases and count >= total_emails * 0.02:  # At least 2% of emails
            recs['new_action_phrases'].append(phrase)
    
    # Suggest new informational phrases
    for phrase, count in informational_phrases_in_content.most_common(10):
        if phrase.lower() not in existing_info_phrases and count >= total_emails * 0.02:
            recs['new_informational_phrases'].append(phrase)
    
    # Analyze patterns
    recs['patterns_found']['question_rate'] = round((question_subjects / total_emails) * 100, 1) if total_emails > 0 else 0
    recs['patterns_found']['reply_rate'] = round((reply_subjects / total_emails) * 100, 1) if total_emails > 0 else 0
    recs['patterns_found']['newsletter_rate'] = round((newsletter_subjects / total_emails) * 100, 1) if total_emails > 0 else 0
    
    return recs


def print_analysis(results: Dict[str, Any]):
    """Print formatted analysis results."""
    
    print("=" * 80)
    print("EMAIL CLASSIFICATION ANALYSIS")
    print("=" * 80)
    print()
    
    print(f"Total emails analyzed: {results['total_emails']}")
    print()
    
    # Category distribution
    print("CATEGORY DISTRIBUTION:")
    print("-" * 40)
    for category, count in results['category_distribution'].items():
        pct = (count / results['total_emails']) * 100
        print(f"  {category:8s}: {count:4d} ({pct:5.1f}%)")
    print()
    
    # Score distribution summary
    if results['score_distribution']:
        scores = list(results['score_distribution'].keys())
        avg = results['recommendations']['patterns_found']['average_score']
        min_s, max_s = results['recommendations']['patterns_found']['score_range']
        print("SCORE STATISTICS:")
        print("-" * 40)
        print(f"  Average score: {avg:.1f}")
        print(f"  Score range:   {min_s} - {max_s}")
        print()
    
    # Top domains
    print("TOP SENDER DOMAINS:")
    print("-" * 40)
    for domain, count in list(results['domain_counter'].items())[:10]:
        pct = (count / results['total_emails']) * 100
        print(f"  {domain:30s}: {count:4d} ({pct:5.1f}%)")
    print()
    
    # Content patterns
    if results.get('action_phrases_in_content'):
        print("ACTION PHRASES FOUND IN CONTENT:")
        print("-" * 40)
        for phrase, count in list(results['action_phrases_in_content'].items())[:10]:
            print(f"  {phrase:30s}: {count:4d}")
        print()
    
    if results.get('informational_phrases_in_content'):
        print("INFORMATIONAL PHRASES FOUND IN CONTENT:")
        print("-" * 40)
        for phrase, count in list(results['informational_phrases_in_content'].items())[:10]:
            print(f"  {phrase:30s}: {count:4d}")
        print()
    
    # Patterns
    patterns = results['recommendations']['patterns_found']
    print("EMAIL PATTERNS:")
    print("-" * 40)
    print(f"  Questions (?):     {patterns.get('question_rate', 0):5.1f}%")
    print(f"  Replies (RE:):     {patterns.get('reply_rate', 0):5.1f}%")
    print(f"  Newsletters:       {patterns.get('newsletter_rate', 0):5.1f}%")
    print()
    
    # Recommendations
    print("RECOMMENDATIONS:")
    print("-" * 40)
    
    # Trusted domains
    if results['recommendations']['trusted_domains']:
        print("\n1. ADD THESE TRUSTED DOMAINS to scoring.py:")
        print("   (These domains appear frequently in your emails)")
        for domain in results['recommendations']['trusted_domains'][:5]:
            print(f"      '{domain}',")
    
    # New action phrases
    if results['recommendations']['new_action_phrases']:
        print("\n2. CONSIDER ADDING THESE ACTION PHRASES to scoring.py:")
        for phrase in results['recommendations']['new_action_phrases'][:5]:
            print(f"      '{phrase}',")
    
    # New informational phrases
    if results['recommendations']['new_informational_phrases']:
        print("\n3. CONSIDER ADDING THESE INFORMATIONAL PHRASES to scoring.py:")
        for phrase in results['recommendations']['new_informational_phrases'][:5]:
            print(f"      '{phrase}',")
    
    # Threshold adjustments
    if results['recommendations']['threshold_adjustments']:
        print("\n4. CONSIDER ADJUSTING CLASSIFICATION THRESHOLDS:")
        for cat, adj in results['recommendations']['threshold_adjustments'].items():
            print(f"   {cat} threshold:")
            print(f"     Current:  {adj['current']}")
            print(f"     Suggested: {adj['suggested']}")
            print(f"     Reason:   {adj['reason']}")
    
    # Misclassified emails
    if results.get('misclassified_emails'):
        print("\n5. POTENTIALLY MISCLASSIFIED EMAILS:")
        print("   (High score but informational content)")
        for email_info in results['misclassified_emails'][:5]:
            print(f"   Score: {email_info['score']} | {email_info['category']}")
            print(f"   From:  {email_info['sender'][:40]}")
            print(f"   Subj:  {email_info['subject'][:60]}")
            if email_info.get('content_preview'):
                print(f"   Content: {email_info['content_preview'][:100]}...")
            print()
    
    # Sample emails
    if results['action_emails']:
        print("\n6. SAMPLE HIGH-SCORING EMAILS (ACTION category):")
        for sender, subject, score, signals, content_preview in results['action_emails'][:5]:
            print(f"   Score: {score}")
            print(f"   From:  {sender[:40]}")
            print(f"   Subj:  {subject[:60]}")
            if content_preview:
                print(f"   Content: {content_preview[:100]}...")
            print()
    
    if results['ignore_emails']:
        print("\n7. SAMPLE LOW-SCORING EMAILS (IGNORE category):")
        for sender, subject, score, signals, content_preview in results['ignore_emails'][:5]:
            print(f"   Score: {score}")
            print(f"   From:  {sender[:40]}")
            print(f"   Subj:  {subject[:60]}")
            if content_preview:
                print(f"   Content: {content_preview[:100]}...")
            print()
    
    print("=" * 80)


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze email patterns to improve classification')
    parser.add_argument('--limit', type=int, default=500, help='Maximum number of emails to analyze (default: 500)')
    parser.add_argument('--since', type=int, help='Analyze emails from the last N days (default: analyze all emails)')
    parser.add_argument('--all', action='store_true', help='Analyze all emails (this is the default behavior)')
    parser.add_argument('--client', choices=['apple-mail', 'outlook', 'auto'], default='auto',
                       help='Email client to use (default: auto-detect)')
    parser.add_argument('--account', type=str, help='Filter by account email address')
    parser.add_argument('--mailbox', type=str, default='Inbox',
                       help='Filter by mailbox/folder name (default: Inbox)')
    
    args = parser.parse_args()
    
    # Default to analyzing all emails unless --since is specified
    since_days = None if (args.all or args.since is None) else args.since
    client = None if args.client == 'auto' else args.client
    
    try:
        results = analyze_emails(
            limit=args.limit,
            since_days=since_days,
            client=client,
            account=args.account,
            mailbox=args.mailbox
        )
        if results:
            print_analysis(results)
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
