"""
1st 4 Mobile — Money Utilities
Currency parsing, GST handling, and financial calculations.
"""

import re
from typing import Optional, Union


GST_RATE = 0.11  # Australian GST (1/11 of GST-inclusive amount)


def parse_amount(value) -> Optional[float]:
    """
    Parse a monetary amount from various string formats.
    
    Handles:
    - "$1,234.56"
    - "1,234.56"
    - "(1,234.56)"  (brackets = negative)
    - "1.234,56"     (European notation — rare)
    - "CR 100.00"    (credit = negative)
    - "-$1,234.56"
    """
    if value is None:
        return None
    
    if isinstance(value, (int, float)):
        return float(value)
    
    s = str(value).strip()
    if not s:
        return None
    
    # Handle credits (CR, Cr, cr prefix/suffix)
    is_credit = bool(re.search(r'\bCR\b', s, re.IGNORECASE))
    s = re.sub(r'\bCR\b', '', s, flags=re.IGNORECASE).strip()
    
    # Handle brackets for negative (Australian convention)
    is_bracket_negative = s.startswith('(') and s.endswith(')')
    s = s.strip('()').strip()
    
    # Remove currency symbols and whitespace
    s = s.replace('$', '').replace('AUD', '').replace('A$', '').strip()
    
    # Handle European notation: 1.234,56 → replace . with '' and , with .
    if re.search(r'\d{1,3}\.\d{3},\d{2}', s):
        s = s.replace('.', '').replace(',', '.')
    else:
        s = s.replace(',', '')
    
    # Remove any remaining non-numeric except minus and dot
    s = re.sub(r'[^\d\.\-]', '', s)
    
    try:
        amount = float(s)
    except ValueError:
        return None
    
    if is_credit or is_bracket_negative:
        amount = -abs(amount)
    
    return round(amount, 2)


def is_gst_inclusive(column_name: str, sample_value: str) -> bool:
    """
    Heuristic: guess if a column values include GST.
    """
    indicators = ['inc gst', 'incl gst', 'gst incl', 'total including']
    col_lower = column_name.lower()
    if any(ind in col_lower for ind in indicators):
        return True
    
    # Check if sample value contains "inc" or similar
    if sample_value:
        sv_lower = sample_value.lower()
        if 'inc gst' in sv_lower or 'incl' in sv_lower:
            return True
    
    return False


def strip_gst(amount: float) -> float:
    """
    Convert GST-inclusive amount to GST-exclusive.
    Australian GST is 10% of the pre-GST amount.
    GST-inclusive ÷ 1.1 = GST-exclusive.
    """
    return round(amount / (1 + GST_RATE), 2)


def format_currency(amount: float) -> str:
    """Format a float as Australian currency string."""
    if amount < 0:
        return f"-${abs(amount):,.2f}"
    return f"${amount:,.2f}"


def format_currency_table(rows: list[tuple[str, float]]) -> str:
    """Format a list of (label, amount) pairs as an aligned table."""
    max_label_len = max(len(r[0]) for r in rows) if rows else 0
    lines = []
    for label, amount in rows:
        label_padded = label.ljust(max_label_len)
        lines.append(f"  {label_padded}  {format_currency(amount)}")
    return '\n'.join(lines)
