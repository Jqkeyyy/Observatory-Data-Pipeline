import subprocess
import sys
import time
import os
import signal
from pathlib import Path

# Dir paths
BACKEND_DIR = Path("backend")
DB_DIR = BACKEND_DIR / "db"
FRONTEND_DIR = Path("frontend/Observtory_Data_Pipeline")
VENV_DIR = BACKEND_DIR / "venv"

if os.name == 'nt':  # Windows
    PYTHON_BIN = (VENV_DIR / "Scripts" / "python.exe").absolute()
    PIP_BIN = (VENV_DIR / "Scripts" / "pip.exe").absolute()
else:  # macOS / Linux
    PYTHON_BIN = (VENV_DIR / "bin" / "python3").absolute()
    PIP_BIN = (VENV_DIR / "bin" / "pip").absolute()

processes = []

def cleanup(signum, frame):
    """ terminate backend and frontend processes on Ctrl+C."""
    print("\n\n Shutting down backend and frontend servers...")
    for p in processes:
        if p.poll() is None:
            p.terminate()
            if os.name == 'nt':
                try:
                    p.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    p.kill()
    sys.exit(0)

signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

def run_cmd(cmd, cwd=None):
    """Run a shell command"""
    result = subprocess.run(cmd, shell=True, cwd=cwd)
    if result.returncode != 0:
        sys.exit(result.returncode)

def install_deps():
    print("Installing Frontend dependencies...\n")
    run_cmd("npm install", cwd=FRONTEND_DIR)

    print("\n\nSetting up Python Virtual environment")
    if not Path(VENV_DIR).exists():
        run_cmd(f"{sys.executable} -m venv venv", cwd=BACKEND_DIR)
        print("\nCreated virtual environment at backend/venv")
    
    print(f"\n\nUpdating virtual environment at {VENV_DIR}...")
    run_cmd(f'"{PIP_BIN}" install --upgrade pip')
    run_cmd(f'"{PIP_BIN}" install -r {BACKEND_DIR / "requirements.txt"}')

def start():
    print("\n\nStarting Database...")
    run_cmd(f'"{PYTHON_BIN}" scripts/setup_db.py', cwd=BACKEND_DIR)

    print("\n\nStarting Server in background...")
    # Server needs to start INSIDE of virtual enviroment
    backend_proc = subprocess.Popen([str(PYTHON_BIN), "server.py"], cwd=str(BACKEND_DIR))
    processes.append(backend_proc)

    print("\n\nStarting Frontend in background...")
    frontend_proc = subprocess.Popen("npm run dev", shell=True, cwd=str(FRONTEND_DIR))
    processes.append(frontend_proc)

    for p in processes:
        p.wait()

def main():
    print("Setting up Local Environment\n\n")
    install_deps()
    start()

if __name__ == "__main__":
    main()