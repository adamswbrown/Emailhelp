"""
classifier.py - Score-to-Category Mapping

CLASSIFICATION RULES:
Maps weighted signal scores (0-100) to actionable categories.

CATEGORIES:
- ACTION:  Score >= 30  - Requires immediate attention/response
- FYI:     Score 20-29  - Informational, may need review
- IGNORE:  Score < 20   - Bulk/automated, can be safely ignored

DETERMINISM:
All classification is rule-based and deterministic.
Same input always produces same output.

RECENT CHANGES:
- 2025-12-30: Lowered ACTION threshold from 40 to 30 based on 60-day email analysis
  (Only 2.2% emails were classified as ACTION with threshold=40)
"""

from enum import Enum
from typing import Tuple


class EmailCategory(Enum):
    """Email classification categories."""
    ACTION = "ACTION"
    FYI = "FYI"
    IGNORE = "IGNORE"


class EmailClassifier:
    """Classify emails based on weighted signal scores."""
    
    # Classification thresholds
    # Updated 2025-12-30: Lowered from 40 to 30 based on email analysis
    # Analysis showed only 2.2% classified as ACTION with threshold=40
    ACTION_THRESHOLD = 30
    FYI_THRESHOLD = 20
    
    @staticmethod
    def classify(score: int) -> EmailCategory:
        """
        Classify an email based on its score.
        
        Args:
            score: Weighted signal score (0-100)
        
        Returns:
            EmailCategory enum value
        """
        if score >= EmailClassifier.ACTION_THRESHOLD:
            return EmailCategory.ACTION
        elif score >= EmailClassifier.FYI_THRESHOLD:
            return EmailCategory.FYI
        else:
            return EmailCategory.IGNORE
    
    @staticmethod
    def classify_with_explanation(score: int) -> Tuple[EmailCategory, str]:
        """
        Classify an email and provide explanation.
        
        Args:
            score: Weighted signal score (0-100)
        
        Returns:
            Tuple of (category, explanation)
        """
        category = EmailClassifier.classify(score)
        
        explanations = {
            EmailCategory.ACTION: f"Score {score} >= {EmailClassifier.ACTION_THRESHOLD} (requires attention)",
            EmailCategory.FYI: f"Score {score} between {EmailClassifier.FYI_THRESHOLD}-{EmailClassifier.ACTION_THRESHOLD-1} (informational)",
            EmailCategory.IGNORE: f"Score {score} < {EmailClassifier.FYI_THRESHOLD} (bulk/automated)",
        }
        
        return category, explanations[category]
    
    @staticmethod
    def get_category_description(category: EmailCategory) -> str:
        """
        Get human-readable description of category.
        
        Args:
            category: EmailCategory enum
        
        Returns:
            Description string
        """
        descriptions = {
            EmailCategory.ACTION: "Requires immediate attention or response",
            EmailCategory.FYI: "Informational, may need review later",
            EmailCategory.IGNORE: "Bulk/automated, can be safely ignored",
        }
        
        return descriptions.get(category, "Unknown category")
