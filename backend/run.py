"""1st 4 Mobile Backend — Entry Point.

Run with:
    cd ~/dev/1st4-mobile && python backend/run.py
"""

import sys
from pathlib import Path

# Ensure project root is on sys.path so 'backend' is importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "backend.server:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        reload_dirs=[str(PROJECT_ROOT)],
        log_level="info",
    )
