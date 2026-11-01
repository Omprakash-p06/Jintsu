#!/usr/bin/env python3
"""Cross-platform full-stack launcher for Reality Check AI (jintru).

Runs natively on Windows, macOS, and Linux without shell dependencies.
Concurrently launches the FastAPI backend and Next.js frontend, monitors
health status, and handles clean graceful shutdowns on SIGINT / Ctrl+C.
"""

import os
import platform
import shutil
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
IS_WINDOWS = platform.system() == "Windows"


def find_python_executable() -> Path:
    venv_dir = ROOT_DIR / "backend" / ".venv"
    if IS_WINDOWS:
        candidate = venv_dir / "Scripts" / "python.exe"
    else:
        candidate = venv_dir / "bin" / "python"

    if candidate.exists():
        return candidate
    return Path(sys.executable)


def find_frontend_command() -> list[str]:
    pnpm_bin = shutil.which("pnpm")
    if pnpm_bin:
        return [pnpm_bin, "dev"]
    npm_bin = shutil.which("npm")
    if npm_bin:
        return [npm_bin, "run", "dev"]
    print("❌ Error: Neither pnpm nor npm was found in PATH.", file=sys.stderr)
    sys.exit(1)


def wait_for_backend(url: str = "http://127.0.0.1:8000/api/v1/health", max_retries: int = 40, delay: float = 0.5) -> bool:
    print(f"Waiting for backend health check at {url}...")
    for _ in range(max_retries):
        try:
            with urllib.request.urlopen(url, timeout=1.0) as resp:
                if resp.status == 200:
                    return True
        except (urllib.error.URLError, TimeoutError, ConnectionRefusedError, OSError):
            time.sleep(delay)
    return False


def terminate_process(proc: subprocess.Popen, name: str) -> None:
    if proc.poll() is not None:
        return
    print(f"Stopping {name} (PID: {proc.pid})...")
    try:
        proc.terminate()
        proc.wait(timeout=3.0)
    except Exception:
        try:
            proc.kill()
            proc.wait(timeout=2.0)
        except Exception:
            pass


def main() -> None:
    print("=" * 70)
    print("🚀 Starting Reality Check AI (jintru) — Cross-Platform Runner")
    print(f"OS: {platform.system()} ({platform.machine()}) | Root: {ROOT_DIR}")
    print("=" * 70)

    # 1. Verify .env exists
    env_file = ROOT_DIR / ".env"
    env_example = ROOT_DIR / ".env.example"
    if not env_file.exists():
        if env_example.exists():
            print("No .env found. Generating from .env.example (mock providers enabled)...")
            shutil.copyfile(env_example, env_file)
            print("✓ Created .env")
        else:
            print("❌ .env file not found. Run 'python setup.py' first.", file=sys.stderr)
            sys.exit(1)

    py_exe = find_python_executable()
    backend_dir = ROOT_DIR / "backend"
    frontend_dir = ROOT_DIR / "frontend"
    frontend_cmd = find_frontend_command()

    backend_proc: subprocess.Popen | None = None
    frontend_proc: subprocess.Popen | None = None

    def shutdown_handler(signum=None, frame=None):
        print("\n🛑 Shutdown requested. Cleaning up child processes...")
        if backend_proc:
            terminate_process(backend_proc, "Backend")
        if frontend_proc:
            terminate_process(frontend_proc, "Frontend")
        print("✓ All processes stopped cleanly. Goodbye!")
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    try:
        # Start Backend via python -m uvicorn
        backend_cmd = [
            str(py_exe),
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "0.0.0.0",
            "--port",
            "8000",
        ]
        print(f"Starting Backend: {' '.join(backend_cmd)} in {backend_dir.name}/")
        backend_proc = subprocess.Popen(
            backend_cmd,
            cwd=backend_dir,
            shell=IS_WINDOWS,
        )

        # Wait until Backend is healthy before starting Frontend
        if not wait_for_backend():
            print("❌ Backend failed to become healthy within timeout.", file=sys.stderr)
            shutdown_handler()

        print("✓ Backend is ready and responding!")

        # Start Frontend
        print(f"Starting Frontend: {' '.join(frontend_cmd)} in {frontend_dir.name}/")
        frontend_proc = subprocess.Popen(
            frontend_cmd,
            cwd=frontend_dir,
            shell=IS_WINDOWS,
        )

        print("\n" + "=" * 70)
        print("✨ Reality Check AI is LIVE!")
        print("   - Frontend Workbench:   http://localhost:3000")
        print("   - Backend REST API:     http://localhost:8000/api/v1")
        print("   - Interactive Swagger:  http://localhost:8000/docs")
        print("=" * 70)
        print("Press Ctrl+C to stop all services.\n")

        # Keep running and monitor process health
        while True:
            if backend_proc.poll() is not None:
                print("❌ Backend process terminated unexpectedly.", file=sys.stderr)
                break
            if frontend_proc.poll() is not None:
                print("❌ Frontend process terminated unexpectedly.", file=sys.stderr)
                break
            time.sleep(1.0)

    except KeyboardInterrupt:
        pass
    finally:
        shutdown_handler()


if __name__ == "__main__":
    main()
