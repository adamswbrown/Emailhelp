#!/usr/bin/env python3
"""
analyze_emails.py - Analyze email patterns to improve classification

This script analyzes your actual emails to:
1. Identify common sender domains
2. Analyze subject line patterns
3. Review score distributions
4. Suggest improvements to scoring signals and thresholds
"""

import sys
from collections import Counter, defaultdict
from typing import List, Dict, Any

from mail_index import MailIndexReader
from scoring import EmailScorer
from classifier import EmailClassifier


def analyze_emails(limit: int = 200, since_days: int = None) -> Dict[str, Any]:
    """
    Analyze email patterns and generate recommendations.
    
    Args:
        limit: Maximum number of emails to analyze
        since_days: Only analyze emails from the last N days (None = all emails)
        
    Returns:
        Dictionary with analysis results and recommendations
    """
    if since_days:
        print(f"Analyzing emails from the last {since_days} days...\n", file=sys.stderr)
    else:
        print("Analyzing your emails...\n", file=sys.stderr)
    
    reader = MailIndexReader()
    scorer = EmailScorer()
    
    with reader:
        messages = reader.query_messages(limit=limit, since_days=since_days)
    
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
    
    # Common patterns to track
    question_subjects = 0
    reply_subjects = 0
    newsletter_subjects = 0
    
    bulk_senders = []
    trusted_senders = []
    action_emails = []
    ignore_emails = []
    
    for msg in messages:
        sender = msg.get('sender', '') or ''
        subject = msg.get('subject', '') or ''
        
        # Extract domain
        if '@' in sender:
            domain = sender.split('@')[1].strip().lower()
            domain_counter[domain] += 1
        
        # Score the email
        score, signals = scorer.score_email(sender, subject)
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
        
        # Track sender patterns
        sender_lower = sender.lower()
        if any(p in sender_lower for p in ['noreply', 'no-reply', 'donotreply']):
            bulk_senders.append((sender, subject, score))
        elif domain in scorer.trusted_domains:
            trusted_senders.append((sender, subject, score))
        
        # Track high/low scoring emails for review
        if score >= 60:
            action_emails.append((sender, subject, score, signals))
        elif score < 30:
            ignore_emails.append((sender, subject, score, signals))
    
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
        ignore_emails
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
    ignore_emails: List
) -> Dict[str, Any]:
    """Generate recommendations based on analysis."""
    
    recs = {
        'trusted_domains': [],
        'threshold_adjustments': {},
        'signal_adjustments': {},
        'patterns_found': {}
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
    
    # Threshold adjustments
    if results['recommendations']['threshold_adjustments']:
        print("\n2. CONSIDER ADJUSTING CLASSIFICATION THRESHOLDS:")
        for cat, adj in results['recommendations']['threshold_adjustments'].items():
            print(f"   {cat} threshold:")
            print(f"     Current:  {adj['current']}")
            print(f"     Suggested: {adj['suggested']}")
            print(f"     Reason:   {adj['reason']}")
    
    # Sample emails
    if results['action_emails']:
        print("\n3. SAMPLE HIGH-SCORING EMAILS (ACTION category):")
        for sender, subject, score, signals in results['action_emails'][:5]:
            print(f"   Score: {score}")
            print(f"   From:  {sender[:40]}")
            print(f"   Subj:  {subject[:60]}")
            print()
    
    if results['ignore_emails']:
        print("\n4. SAMPLE LOW-SCORING EMAILS (IGNORE category):")
        for sender, subject, score, signals in results['ignore_emails'][:5]:
            print(f"   Score: {score}")
            print(f"   From:  {sender[:40]}")
            print(f"   Subj:  {subject[:60]}")
            print()
    
    print("=" * 80)


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze email patterns to improve classification')
    parser.add_argument('--limit', type=int, default=500, help='Maximum number of emails to analyze (default: 500)')
    parser.add_argument('--since', type=int, default=30, help='Analyze emails from the last N days (default: 30)')
    parser.add_argument('--all', action='store_true', help='Analyze all emails (ignore --since)')
    
    args = parser.parse_args()
    
    since_days = None if args.all else args.since
    
    try:
        results = analyze_emails(limit=args.limit, since_days=since_days)
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

