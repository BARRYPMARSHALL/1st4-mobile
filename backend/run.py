"""1st 4 Mobile Backend — Entry Point.

Run with:
    cd ~/dev/1st4-mobile && python backend/run.py
"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "backend.server:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info",
    )
