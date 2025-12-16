import sys
import os
from fastapi.testclient import TestClient

# Add parent dir to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

try:
    from agent.app import app
    print("App imported successfully")
    
    client = TestClient(app)
    response = client.get("/health")
    print(f"Health check status: {response.status_code}")
    # It might return 401 or whatever because of guard, or just work.
    # guard checks authorization header.
    # But correct import is the main thing here.
    
    print("APP LOAD SUCCESSFUL")

except ImportError as e:
    print(f"IMPORT ERROR: {e}")
    sys.exit(1)
except Exception as e:
    print(f"RUNTIME ERROR: {e}")
    sys.exit(1)
