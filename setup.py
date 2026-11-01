#!/usr/bin/env python3
"""Cross-platform setup script for Reality Check AI (jintru).

Runs natively on Windows, macOS, and Linux without shell dependencies.
Sets up the Python virtual environment, dependencies, frontend packages,
environment configuration, and pre-initializes the local SQLite database.
"""

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent


def print_step(msg: str) -> None:
    print(f"\n=== {msg} ===")


def run_command(cmd: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    cwd_path = cwd or ROOT_DIR
    cmd_str = " ".join(str(c) for c in cmd)
    print(f"-> Running: {cmd_str} (in {cwd_path.name})")
    # On Windows, commands like npm/pnpm need shell=True or .cmd extension
    is_windows = platform.system() == "Windows"
    return subprocess.run(cmd, cwd=cwd_path, check=check, shell=is_windows)


def main() -> None:
    print("=" * 70)
    print("Reality Check AI (jintru) — Universal Cross-Platform Setup")
    print(f"Platform: {platform.system()} ({platform.machine()}) | Python: {platform.python_version()}")
    print("=" * 70)

    # 1. Check Python version
    print_step("[1/5] Checking System Prerequisites")
    if sys.version_info < (3, 11):
        print(f"❌ Python >= 3.11 is required. Found: {platform.python_version()}", file=sys.stderr)
        sys.exit(1)
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} satisfies requirements.")

    # Check Node.js
    node_bin = shutil.which("node")
    if not node_bin:
        print("❌ Node.js is required but was not found in PATH.", file=sys.stderr)
        print("   Please install Node.js 20+ from https://nodejs.org", file=sys.stderr)
        sys.exit(1)

    try:
        node_ver_res = subprocess.run([node_bin, "-v"], capture_output=True, text=True, check=True)
        node_ver_str = node_ver_res.stdout.strip()
        print(f"✓ Node.js found: {node_ver_str}")
    except Exception as exc:
        print(f"⚠ Warning: Could not determine Node.js version: {exc}")

    # 2. Check / Initialize .env
    print_step("[2/5] Initializing Environment Configuration")
    env_file = ROOT_DIR / ".env"
    env_example = ROOT_DIR / ".env.example"
    if not env_file.exists():
        if env_example.exists():
            print("Creating .env from .env.example (mock providers enabled by default)...")
            shutil.copyfile(env_example, env_file)
            print("✓ Created .env")
        else:
            print("⚠ Warning: .env.example not found; skipping .env creation.")
    else:
        print("✓ Existing .env file found.")

    # 3. Virtual Environment Setup
    print_step("[3/5] Setting up Python Virtual Environment & Dependencies")
    venv_dir = ROOT_DIR / "backend" / ".venv"
    if platform.system() == "Windows":
        venv_python = venv_dir / "Scripts" / "python.exe"
        venv_pip = venv_dir / "Scripts" / "pip.exe"
        venv_pytest = venv_dir / "Scripts" / "pytest.exe"
    else:
        venv_python = venv_dir / "bin" / "python"
        venv_pip = venv_dir / "bin" / "pip"
        venv_pytest = venv_dir / "bin" / "pytest"

    if not venv_dir.exists():
        print(f"Creating virtual environment in {venv_dir}...")
        import venv
        venv.create(venv_dir, with_pip=True)
        print("✓ Virtual environment created.")
    else:
        print("✓ Existing virtual environment found.")

    print("Upgrading pip and installing backend dependencies...")
    run_command([str(venv_pip), "install", "--upgrade", "pip", "setuptools", "wheel"])
    run_command([str(venv_pip), "install", "-e", "backend[dev]"])
    print("✓ Backend Python packages installed.")

    # 4. Frontend Dependencies Setup
    print_step("[4/5] Setting up Frontend Dependencies")
    frontend_dir = ROOT_DIR / "frontend"
    pnpm_bin = shutil.which("pnpm")
    npm_bin = shutil.which("npm")

    if pnpm_bin:
        print("Installing frontend packages via pnpm...")
        run_command([pnpm_bin, "install"], cwd=frontend_dir)
    elif npm_bin:
        print("Installing frontend packages via npm...")
        run_command([npm_bin, "install"], cwd=frontend_dir)
    else:
        print("❌ Neither pnpm nor npm was found in PATH.", file=sys.stderr)
        sys.exit(1)
    print("✓ Frontend packages installed.")

    # 5. Database Initialization & Smoke Tests
    print_step("[5/5] Initializing Database & Running Smoke Tests")
    data_dir = ROOT_DIR / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    init_script = (
        "import asyncio\n"
        "from app.db.database import Database\n"
        "async def init():\n"
        "    db = Database('data/jintru.db')\n"
        "    await db.init_db()\n"
        "    print('✓ SQLite WAL database verified at data/jintru.db')\n"
        "asyncio.run(init())\n"
    )
    subprocess.run([str(venv_python), "-c", init_script], cwd=ROOT_DIR, check=True)

    print("Running backend smoke tests...")
    run_command([str(venv_pytest), "backend/tests/unit/test_schemas.py", "-q"])
    print("✓ Smoke test passed.")

    print("\n" + "=" * 70)
    print("🎉 Project setup complete on " + platform.system() + "!")
    print("   To launch both backend and frontend, run:")
    print("      python run.py")
    print("=" * 70)


if __name__ == "__main__":
    main()
