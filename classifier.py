"""
classifier.py - Score-to-Category Mapping

CLASSIFICATION RULES:
Maps weighted signal scores (0-100) to actionable categories.

CATEGORIES:
- ACTION:  Score >= 60  - Requires immediate attention/response
- FYI:     Score 30-59  - Informational, may need review
- IGNORE:  Score < 30   - Bulk/automated, can be safely ignored

DETERMINISM:
All classification is rule-based and deterministic.
Same input always produces same output.
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
    ACTION_THRESHOLD = 40
    FYI_THRESHOLD = 30
    
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
