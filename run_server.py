import sys
import os
import uvicorn

# Add the current directory to the python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

if __name__ == "__main__":
    uvicorn.run("bounty_command_center.main:app", host="0.0.0.0", port=8000, reload=True)
