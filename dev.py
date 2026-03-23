import subprocess
import sys
import os

def run_dev():
    print("Starting BBS Development Environment...")
    
    # 1. Start the server with uvicorn reload
    # We use uvicorn directly to ensure reload works as expected
    server_cmd = [
        sys.executable, "-m", "uvicorn", 
        "bbs_server:app", 
        "--host", "0.0.0.0", 
        "--port", "8100", 
        "--reload"
    ]
    
    # 2. Start the client with textual dev mode
    # Note: This requires 'textual' to be installed and in the PATH
    client_cmd = [
        sys.executable, "-m", "textual", "run", "--dev", "bbs_client.app"
    ]
    
    print(f"Server command: {' '.join(server_cmd)}")
    print(f"Client command: {' '.join(client_cmd)}")
    
    try:
        # Start server in background
        server_proc = subprocess.Popen(server_cmd)
        
        # Start client (blocking)
        # Note: In a real terminal, you'd probably want to run these in separate panes/windows
        # but for a single script, we'll try to run them together or provide instructions.
        print("\n--- Instructions ---")
        print("To see live CSS/Layout changes in the client:")
        print("1. In one terminal, run: textual console")
        print("2. In another terminal, run: textual run --dev bbs_client/app.py")
        print("\nStarting client now...")
        
        subprocess.run(client_cmd)
        
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        server_proc.terminate()

if __name__ == "__main__":
    run_dev()
