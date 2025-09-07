import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

# Import the Flask app
from app import create_app

# Create the application
application = create_app()

if __name__ == "__main__":
    application.run()
