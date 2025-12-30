#!/usr/bin/env python3
"""
analyze_and_update.py - Analyze emails and automatically update scoring rules

This script:
1. Analyzes your emails
2. Identifies patterns and common domains
3. Automatically updates scoring.py with recommended changes
"""

import sys
import re
from collections import Counter
from typing import List, Dict, Any

from mail_index import MailIndexReader
from scoring import EmailScorer
from classifier import EmailClassifier


def analyze_and_get_updates(limit: int = 500, since_days: int = 30) -> Dict[str, Any]:
    """Analyze emails and return recommended updates."""
    
    print(f"Analyzing emails from the last {since_days} days...\n", file=sys.stderr)
    
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
    score_distribution = Counter()
    category_distribution = Counter()
    
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
        
        score_distribution[score] += 1
        category_distribution[category.value] += 1
    
    # Generate recommendations
    total_emails = len(messages)
    
    # Find domains to add (appear in at least 2% of emails and not already trusted)
    domains_to_add = []
    for domain, count in domain_counter.most_common(20):
        pct = (count / total_emails) * 100
        if domain not in scorer.trusted_domains and pct >= 2.0:
            domains_to_add.append(domain)
    
    # Analyze score distribution
    scores = list(score_distribution.keys())
    avg_score = sum(s * count for s, count in score_distribution.items()) / sum(score_distribution.values()) if scores else 0
    
    action_count = category_distribution.get('ACTION', 0)
    fyi_count = category_distribution.get('FYI', 0)
    ignore_count = category_distribution.get('IGNORE', 0)
    
    action_pct = (action_count / total_emails) * 100 if total_emails > 0 else 0
    
    # Suggest threshold adjustments
    threshold_adjustment = None
    if action_pct < 10:
        threshold_adjustment = -10  # Lower threshold
    elif action_pct > 40:
        threshold_adjustment = +10  # Raise threshold
    
    return {
        'domains_to_add': domains_to_add[:10],  # Top 10
        'threshold_adjustment': threshold_adjustment,
        'stats': {
            'total_emails': total_emails,
            'avg_score': round(avg_score, 1),
            'action_pct': round(action_pct, 1),
            'fyi_pct': round((fyi_count / total_emails) * 100, 1) if total_emails > 0 else 0,
            'ignore_pct': round((ignore_count / total_emails) * 100, 1) if total_emails > 0 else 0,
        }
    }


def update_scoring_py(domains_to_add: List[str], scoring_file: str = 'scoring.py'):
    """Update scoring.py with new trusted domains."""
    
    print(f"\nUpdating {scoring_file}...", file=sys.stderr)
    
    with open(scoring_file, 'r') as f:
        content = f.read()
    
    # Find the TRUSTED_DOMAINS list
    pattern = r"(TRUSTED_DOMAINS\s*=\s*\[)(.*?)(\s*\])"
    match = re.search(pattern, content, re.DOTALL)
    
    if not match:
        print(f"Could not find TRUSTED_DOMAINS in {scoring_file}", file=sys.stderr)
        return False
    
    start = match.start(1)
    end = match.end(3)
    existing_list = match.group(2)
    
    # Parse existing domains
    existing_domains = re.findall(r"'([^']+)'", existing_list)
    
    # Add new domains (avoid duplicates)
    all_domains = existing_domains.copy()
    for domain in domains_to_add:
        if domain not in all_domains:
            all_domains.append(domain)
    
    # Rebuild the list
    domain_lines = [f"        '{domain}'," for domain in all_domains]
    new_list = '\n' + '\n'.join(domain_lines) + '\n    '
    
    new_content = content[:start] + match.group(1) + new_list + match.group(3) + content[end:]
    
    with open(scoring_file, 'w') as f:
        f.write(new_content)
    
    print(f"Added {len(domains_to_add)} new domains to TRUSTED_DOMAINS", file=sys.stderr)
    return True


def update_classifier_py(threshold_adjustment: int, classifier_file: str = 'classifier.py'):
    """Update classifier.py with threshold adjustments."""
    
    if threshold_adjustment is None:
        return False
    
    print(f"\nUpdating {classifier_file}...", file=sys.stderr)
    
    with open(classifier_file, 'r') as f:
        content = f.read()
    
    # Find ACTION_THRESHOLD
    pattern = r'(ACTION_THRESHOLD\s*=\s*)(\d+)'
    match = re.search(pattern, content)
    
    if match:
        current_threshold = int(match.group(2))
        new_threshold = max(30, min(90, current_threshold + threshold_adjustment))
        
        new_content = content[:match.start(2)] + str(new_threshold) + content[match.end(2):]
        
        with open(classifier_file, 'w') as f:
            f.write(new_content)
        
        print(f"Updated ACTION_THRESHOLD: {current_threshold} -> {new_threshold}", file=sys.stderr)
        return True
    
    return False


def print_summary(updates: Dict[str, Any]):
    """Print summary of updates."""
    
    print("\n" + "=" * 80)
    print("ANALYSIS SUMMARY")
    print("=" * 80)
    print(f"\nTotal emails analyzed: {updates['stats']['total_emails']}")
    print(f"Average score: {updates['stats']['avg_score']}")
    print(f"\nCategory distribution:")
    print(f"  ACTION: {updates['stats']['action_pct']:.1f}%")
    print(f"  FYI:    {updates['stats']['fyi_pct']:.1f}%")
    print(f"  IGNORE: {updates['stats']['ignore_pct']:.1f}%")
    
    if updates['domains_to_add']:
        print(f"\nDomains to add: {len(updates['domains_to_add'])}")
        for domain in updates['domains_to_add']:
            print(f"  - {domain}")
    
    if updates['threshold_adjustment']:
        print(f"\nThreshold adjustment: {updates['threshold_adjustment']:+d}")
    
    print("=" * 80)


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze emails and update scoring rules')
    parser.add_argument('--limit', type=int, default=500, help='Maximum number of emails to analyze')
    parser.add_argument('--since', type=int, default=30, help='Analyze emails from the last N days')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be updated without making changes')
    
    args = parser.parse_args()
    
    try:
        updates = analyze_and_get_updates(limit=args.limit, since_days=args.since)
        
        if not updates:
            print("No updates needed or no emails found.", file=sys.stderr)
            return 0
        
        print_summary(updates)
        
        if args.dry_run:
            print("\n[DRY RUN] No files were modified. Remove --dry-run to apply changes.")
            return 0
        
        # Apply updates
        if updates['domains_to_add']:
            update_scoring_py(updates['domains_to_add'])
        
        if updates['threshold_adjustment']:
            update_classifier_py(updates['threshold_adjustment'])
        
        print("\n✓ Rules updated successfully!")
        return 0
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())


