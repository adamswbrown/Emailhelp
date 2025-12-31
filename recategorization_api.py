# Methods to add to EmailTriageAPI class for re-categorization

def run_evaluation(self, days: int = 60, limit: int = 500):
    """
    Run categorization evaluation on recent emails.
    
    Args:
        days: Number of days to analyze
        limit: Maximum emails to analyze
        
    Returns:
        JSON with evaluation results and suggestions
    """
    import sys
    from analyze_emails import analyze_emails
    
    try:
        print(f"[API] Running evaluation: days={days}, limit={limit}", file=sys.stderr)
        
        # Run analysis
        results = analyze_emails(
            limit=limit,
            since_days=days,
            client=self.client if self.client != 'auto' else None,
            account=self.account
        )
        
        if not results:
            return json.dumps({
                "success": False,
                "message": "No emails found to analyze"
            })
        
        # Extract key metrics
        total = results.get('total_emails', 0)
        categories = results.get('category_distribution', {})
        recommendations = results.get('recommendations', {})
        
        return json.dumps({
            "success": True,
            "total_emails": total,
            "categories": dict(categories),
            "score_stats": {
                "average": recommendations.get('patterns_found', {}).get('average_score', 0),
                "range": recommendations.get('patterns_found', {}).get('score_range', [0, 0])
            },
            "suggestions": {
                "trusted_domains": recommendations.get('trusted_domains', [])[:5],
                "threshold_adjustments": recommendations.get('threshold_adjustments', {}),
                "action_phrases": list(results.get('action_phrases_in_content', {}).items())[:10],
                "info_phrases": list(results.get('informational_phrases_in_content', {}).items())[:10]
            },
            "patterns": recommendations.get('patterns_found', {})
        })
        
    except Exception as e:
        print(f"[API] Evaluation error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return json.dumps({
            "success": False,
            "message": f"Evaluation failed: {str(e)}"
        })

def get_current_thresholds(self):
    """Get current categorization thresholds."""
    return json.dumps({
        "action_threshold": self.classifier.ACTION_THRESHOLD,
        "fyi_threshold": self.classifier.FYI_THRESHOLD
    })

def apply_threshold_adjustment(self, new_action_threshold: int):
    """
    Apply new ACTION threshold (requires manual file edit for persistence).
    
    Args:
        new_action_threshold: New threshold value (20-90)
        
    Returns:
        JSON with result
    """
    try:
        # Validate
        if new_action_threshold < 20 or new_action_threshold > 90:
            return json.dumps({
                "success": False,
                "message": "Threshold must be between 20 and 90"
            })
        
        old_threshold = self.classifier.ACTION_THRESHOLD
        
        # Update in-memory (not persistent - needs file edit)
        self.classifier.ACTION_THRESHOLD = new_action_threshold
        
        return json.dumps({
            "success": True,
            "message": f"Threshold updated from {old_threshold} to {new_action_threshold} (in-memory only)",
            "note": "This change is temporary. To make it permanent, edit classifier.py"
        })
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "message": str(e)
        })
