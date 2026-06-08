"""
1st 4 Mobile — Date Utilities
Handles Australian date format ambiguity and parsing.
"""

import re
from datetime import datetime, date
from typing import Optional


# Date format patterns in priority order
DATE_PATTERNS = [
    (r'^(\d{2})/(\d{2})/(\d{4})$', 'DD/MM/YYYY'),
    (r'^(\d{1,2})-([A-Za-z]{3})-(\d{4})$', 'DD-Mon-YYYY'),
    (r'^(\d{4})-(\d{2})-(\d{2})$', 'YYYY-MM-DD'),
    (r'^(\d{2})/(\d{2})/(\d{2})$', 'DD/MM/YY'),
    (r'^(\d{2})\.(\d{2})\.(\d{4})$', 'DD.MM.YYYY'),
    (r'^(\d{4})(\d{2})(\d{2})$', 'YYYYMMDD'),
]


def parse_date(value, prefer_au: bool = True) -> Optional[date]:
    """
    Parse a date string using known Australian formats.
    
    Args:
        value: Date string or datetime object
        prefer_au: If True, interpret DD/MM/YYYY over MM/DD/YYYY
    
    Returns:
        date object or None if parsing fails
    """
    if value is None:
        return None
    
    if isinstance(value, (datetime, date)):
        return value if isinstance(value, date) else value.date()
    
    s = str(value).strip()
    if not s:
        return None
    
    for pattern, fmt_name in DATE_PATTERNS:
        match = re.match(pattern, s)
        if match:
            try:
                if fmt_name == 'DD/MM/YYYY':
                    d, m, y = int(match.group(1)), int(match.group(2)), int(match.group(3))
                    if m > 12 and prefer_au:
                        # Ambiguous — assume DD/MM/YYYY as specified
                        pass
                    return date(y, m, d)
                elif fmt_name == 'DD/MM/YY':
                    d, m, y = int(match.group(1)), int(match.group(2)), int(match.group(3))
                    y += 2000 if y < 50 else 1900
                    return date(y, m, d)
                elif fmt_name == 'DD-Mon-YYYY':
                    return datetime.strptime(s, '%d-%b-%Y').date()
                elif fmt_name == 'YYYY-MM-DD':
                    return datetime.strptime(s, '%Y-%m-%d').date()
                elif fmt_name == 'DD.MM.YYYY':
                    d, m, y = int(match.group(1)), int(match.group(2)), int(match.group(3))
                    return date(y, m, d)
                elif fmt_name == 'YYYYMMDD':
                    return datetime.strptime(s, '%Y%m%d').date()
            except (ValueError, IndexError):
                continue
    
    # Try pandas parse as last resort
    try:
        import pandas as pd
        parsed = pd.to_datetime(s, dayfirst=prefer_au, errors='coerce')
        if pd.notna(parsed):
            return parsed.date()
    except ImportError:
        pass
    
    return None


def is_date_ambiguous(raw_date: str) -> bool:
    """
    Check if a date string could be misinterpreted (DD/MM vs MM/DD).
    """
    match = re.match(r'^(\d{2})/(\d{2})/', raw_date)
    if match:
        day, month = int(match.group(1)), int(match.group(2))
        if day <= 12 and month <= 12:
            return True
    return False


def months_between(start: date, end: date) -> int:
    """Calculate whole calendar months between two dates."""
    return (end.year - start.year) * 12 + (end.month - start.month)
