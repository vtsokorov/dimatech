#!/usr/bin/env python3
"""
Main entry point for Payment API application.
This script can be used to run the application locally without Docker.
"""

import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.main import app

if __name__ == "__main__":
    # Run with uvicorn for production-like environment
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)