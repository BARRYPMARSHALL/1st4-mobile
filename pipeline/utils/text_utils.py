"""
1st 4 Mobile — Text Utilities
Fuzzy matching, string cleaning, and pattern detection.
"""

import re
from typing import Optional


def clean_string(s: str) -> str:
    """Normalise whitespace and strip special characters."""
    if not s:
        return ""
    s = re.sub(r'\s+', ' ', s)  # Collapse multiple spaces
    s = s.strip()
    return s


def fuzzy_column_match(column_name: str, known_patterns: list[str],
                       threshold: int = 80) -> Optional[str]:
    """
    Match a column name against known patterns using fuzzy matching.
    
    Args:
        column_name: Raw column name to match
        known_patterns: List of known pattern strings
        threshold: Minimum similarity score (0-100)
    
    Returns:
        Best matching pattern or None
    
    Note: Uses Levenshtein distance via thefuzz library.
    Falls back to substring matching if thefuzz is not available.
    """
    col_clean = clean_string(column_name).lower()
    
    try:
        from thefuzz import fuzz
        best_score = 0
        best_match = None
        for pattern in known_patterns:
            score = fuzz.ratio(col_clean, pattern.lower())
            if score > best_score:
                best_score = score
                best_match = pattern
        return best_match if best_score >= threshold else None
    
    except ImportError:
        # Fall back to substring matching
        for pattern in known_patterns:
            if pattern.lower() in col_clean or col_clean in pattern.lower():
                return pattern
        return None


def extract_plan_code(text: str) -> Optional[str]:
    """
    Extract a plan code from a charge description string.
    Telstra/Optus plan codes often look like: MBP-50GB, DATA-50GB-SHARED, etc.
    """
    # Match common plan code patterns
    patterns = [
        r'([A-Z]{2,6}[-][A-Za-z0-9\-]+)',  # MBP-50GB-POOL, DATA-1GB
        r'(Plan\s*[A-Z0-9\-]+)',             # Plan MBP50
        r'([A-Z]{2,6}\d+[A-Za-z]*)',         # MBP50, IOT1GB
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def classify_service_type(description: str, plan_code: str = "") -> str:
    """
    Classify service type from description + plan code.
    Returns: mobile, data, iot, satellite, fixed_line, voice, unknown
    """
    combined = f"{description} {plan_code}".lower()
    
    if any(w in combined for w in ['satellite', 'sat']):
        return 'satellite'
    if any(w in combined for w in ['iot', 'm2m', 'sensor', 'telemetry']):
        return 'iot'
    if any(w in combined for w in ['fixed', 'landline', 'pstn', 'isdn']):
        return 'fixed_line'
    if any(w in combined for w in ['data only', 'broadband', 'nbn', 'data sim']):
        return 'data'
    if any(w in combined for w in ['voice only', 'voice plan']):
        return 'voice'
    if any(w in combined for w in ['mobile', 'sim', 'handset', 'smartphone']):
        return 'mobile'
    
    return 'unknown'


def classify_charge_category(description: str, amount: float) -> str:
    """
    Classify a charge into a category.
    Returns: monthly_access, usage, roaming, overage, equipment, 
             disconnect, late_fee, credit, other
    """
    desc_lower = description.lower()
    
    if amount < 0:
        return 'credit'
    
    if any(w in desc_lower for w in ['roam', 'international']):
        return 'roaming'
    
    if any(w in desc_lower for w in ['overage', 'excess', 'extra data', 'additional usage']):
        return 'overage'
    
    if any(w in desc_lower for w in ['disconnect', 'deactivation', 'termination', 'cancellation']):
        return 'disconnect'
    
    if any(w in desc_lower for w in ['late', 'penalty', 'fee']):
        return 'late_fee'
    
    if any(w in desc_lower for w in ['handset', 'device', 'hardware', 'phone', 'tablet', 'modem']):
        return 'equipment'
    
    if any(w in desc_lower for w in ['access', 'plan fee', 'subscription', 'monthly', 'service fee']):
        return 'monthly_access'
    
    if any(w in desc_lower for w in ['usage', 'call', 'sms', 'data', 'mb', 'gb', 'minute']):
        return 'usage'
    
    return 'other'


def extract_charge_type_from_description(description: str) -> str:
    """
    For roaming charges: classify as data/voice/sms.
    """
    desc_lower = description.lower()
    if any(w in desc_lower for w in ['data', 'mb', 'gb', 'megabyte', 'gigabyte']):
        return 'data'
    if any(w in desc_lower for w in ['voice', 'call', 'minute', 'talk']):
        return 'voice'
    if any(w in desc_lower for w in ['sms', 'text', 'message']):
        return 'sms'
    return 'data'  # default
