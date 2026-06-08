"""
1st 4 Mobile — Logging Utilities
Audit trail logging for pipeline operations.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime


def setup_logging(log_dir: str = None, level: str = "INFO",
                  verbose: bool = False) -> logging.Logger:
    """
    Set up pipeline logging.
    
    Args:
        log_dir: Directory for log files. None = stdout only.
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        verbose: If True, show debug-level output
    
    Returns:
        Configured logger
    """
    log_level = logging.DEBUG if verbose else getattr(logging, level.upper(), logging.INFO)
    
    logger = logging.getLogger('1st4pipeline')
    logger.setLevel(log_level)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Console handler
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(log_level)
    console.setFormatter(logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%H:%M:%S'
    ))
    logger.addHandler(console)
    
    # File handler (if log_dir specified)
    if log_dir:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_handler = logging.FileHandler(
            log_path / f"audit_{timestamp}.log", encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(module)s:%(lineno)d | %(message)s'
        ))
        logger.addHandler(file_handler)
    
    return logger


class AuditLogger:
    """
    Structured audit trail for each pipeline run.
    Records: files processed, rows ingested, flags generated, outputs created.
    """
    
    def __init__(self):
        self.events = []
    
    def log(self, stage: str, action: str, detail: str, 
            count: int = None, amount: float = None):
        """Record an audit event."""
        self.events.append({
            'timestamp': datetime.now().isoformat(),
            'stage': stage,
            'action': action,
            'detail': detail,
            'count': count,
            'amount': amount,
        })
    
    def summary(self) -> str:
        """Generate a human-readable audit summary."""
        lines = ["\n=== AUDIT TRAIL ==="]
        for ev in self.events:
            parts = [f"[{ev['stage']}] {ev['action']}: {ev['detail']}"]
            if ev['count'] is not None:
                parts.append(f" ({ev['count']} items)")
            if ev['amount'] is not None:
                parts.append(f" ${ev['amount']:.2f}")
            lines.append(''.join(parts))
        return '\n'.join(lines)
