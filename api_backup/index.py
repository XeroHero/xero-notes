import sys
import os

# Add the backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app', 'backend'))

# Import and run the FastAPI app
from server import app

# Vercel serverless function handler
def handler(request):
    return app(request.scope, request.receive, request.send)
