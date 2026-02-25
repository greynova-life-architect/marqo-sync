import os
import sys
import subprocess
import time
import signal
import platform
from pathlib import Path

def get_script_dir():
    return Path(__file__).parent.absolute()

def start_backend():
    script_dir = get_script_dir()
    backend_process = subprocess.Popen(
        [sys.executable, "run_api.py"],
        cwd=script_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    return backend_process

def check_frontend_dependencies():
    script_dir = get_script_dir()
    frontend_dir = script_dir / "frontend"
    node_modules = frontend_dir / "node_modules"
    
    if not node_modules.exists():
        print("Frontend dependencies not installed. Installing...")
        if platform.system() == "Windows":
            npm_cmd = "npm.cmd"
        else:
            npm_cmd = "npm"
        
        install_process = subprocess.run(
            [npm_cmd, "install"],
            cwd=frontend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if install_process.returncode != 0:
            print(f"Failed to install frontend dependencies: {install_process.stderr}")
            return False
        
        print("Frontend dependencies installed successfully.")
    
    return True

def start_frontend():
    script_dir = get_script_dir()
    frontend_dir = script_dir / "frontend"
    
    if not frontend_dir.exists():
        print("Frontend directory not found. Please ensure 'frontend' directory exists.")
        return None
    
    if not check_frontend_dependencies():
        return None
    
    if platform.system() == "Windows":
        npm_cmd = "npm.cmd"
    else:
        npm_cmd = "npm"
    
    frontend_process = subprocess.Popen(
        [npm_cmd, "run", "dev"],
        cwd=frontend_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    return frontend_process

def print_output(process, name):
    if process.stdout:
        for line in iter(process.stdout.readline, ''):
            if line:
                print(f"[{name}] {line.rstrip()}")
    if process.stderr:
        for line in iter(process.stderr.readline, ''):
            if line:
                print(f"[{name}] ERROR: {line.rstrip()}")

def main():
    print("Starting Marqo Sync Services...")
    print("=" * 50)
    
    backend_process = None
    frontend_process = None
    
    try:
        print("Starting backend API server...")
        backend_process = start_backend()
        time.sleep(2)
        
        if backend_process.poll() is not None:
            print("Backend failed to start!")
            if backend_process.stderr:
                print(backend_process.stderr.read())
            return
        
        print("Backend started on http://localhost:8000")
        print("Starting frontend development server...")
        
        frontend_process = start_frontend()
        time.sleep(3)
        
        if frontend_process and frontend_process.poll() is not None:
            print("Frontend failed to start!")
            if frontend_process.stderr:
                print(frontend_process.stderr.read())
            return
        
        print("Frontend started on http://localhost:3000")
        print("=" * 50)
        print("Services running!")
        print("Backend API: http://localhost:8000")
        print("Frontend UI: http://localhost:3000")
        print("Press Ctrl+C to stop all services")
        print("=" * 50)
        
        import threading
        
        def read_backend():
            if backend_process.stdout:
                for line in iter(backend_process.stdout.readline, ''):
                    if line:
                        print(f"[BACKEND] {line.rstrip()}")
        
        def read_frontend():
            if frontend_process and frontend_process.stdout:
                for line in iter(frontend_process.stdout.readline, ''):
                    if line:
                        print(f"[FRONTEND] {line.rstrip()}")
        
        backend_thread = threading.Thread(target=read_backend, daemon=True)
        frontend_thread = threading.Thread(target=read_frontend, daemon=True)
        
        backend_thread.start()
        if frontend_process:
            frontend_thread.start()
        
        while True:
            if backend_process.poll() is not None:
                print("Backend process ended!")
                break
            if frontend_process and frontend_process.poll() is not None:
                print("Frontend process ended!")
                break
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nShutting down services...")
    finally:
        if backend_process:
            print("Stopping backend...")
            backend_process.terminate()
            try:
                backend_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                backend_process.kill()
        
        if frontend_process:
            print("Stopping frontend...")
            frontend_process.terminate()
            try:
                frontend_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                frontend_process.kill()
        
        print("All services stopped.")

if __name__ == "__main__":
    main()

