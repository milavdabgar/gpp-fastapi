#!/usr/bin/env python3
import os
import sys
import logging
import argparse
import uvicorn
from app.config import HOST, PORT, DEBUG

# Set up logging
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

def main():
    """
    Run the FastAPI application
    """
    parser = argparse.ArgumentParser(description="Run the FastAPI application")
    parser.add_argument('--host', type=str, default=HOST, help='Host to bind to')
    parser.add_argument('--port', type=int, default=PORT, help='Port to bind to')
    parser.add_argument('--reload', action='store_true', help='Enable auto-reload')
    args = parser.parse_args()
    
    # Ensure reload is enabled in development mode
    reload_enabled = args.reload or DEBUG
    
    logger.info(f"Starting FastAPI application on {args.host}:{args.port}")
    logger.info(f"Debug mode: {DEBUG}")
    logger.info(f"Auto-reload: {reload_enabled}")
    
    # Run the application
    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=reload_enabled,
        log_level="debug" if DEBUG else "info",
    )

if __name__ == "__main__":
    main()