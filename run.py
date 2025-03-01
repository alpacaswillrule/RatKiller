#!/usr/bin/env python3
"""
Run script for the Rat Reporter application.
This script starts the Flask backend server.
"""

import os
import sys

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Import the Flask app
from app import app

if __name__ == '__main__':
    # Run the Flask app
    app.run(debug=True, host='0.0.0.0', port=5001)
