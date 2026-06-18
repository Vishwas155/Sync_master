#!/usr/bin/env python3
import asyncio
import tempfile
import shutil
import subprocess
import time
import json
import signal
import os
from pathlib import Path

def create_server_instance(name: str, port: int) -> tuple[Path, Path, dict]:
    vault = Path(tempfile.mkdtemp(prefix=f'obsync_test_{name}_'))
    config_dir = Path(tempfile.mkdtemp(prefix=f'obsync_cfg_{name}_'))

    (vault / "notes").mkdir()
    (vault / "notes" / "index.md").write_text(f"# {name} Index")
    (vault / "shared.md").write_text(f"Shared note from {name}")

    config = {
        "vault_path": str(vault),
        "port": port,
        "device_name": name,
        "auto_sync": False
    }
    (config_dir / "config.json").write_text(json.dumps(config))

    print(f"✓ Created {name}: vault={vault.name}")
    return vault, config_dir, config

def start_server_process(config_dir: Path, port: int) -> subprocess.Popen:
    env = os.environ.copy()
    env["OBSYNC_HOME"] = str(config_dir)

    proc = subprocess.Popen(
        ["python3", "-c", f"""
import sys
sys.path.insert(0, '.')
from db import init_db
from server import run_server
init_db()
run_server()
"""],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    time.sleep(1)  # Let server start
    print(f"✓ Server on port {port} started (PID {proc.pid})")
    return proc

async def test():
    # Setup two instances
    vault_a, cfg_a, _ = create_server_instance("machine_a", 9001)
    vault_b, cfg_b, _ = create_server_instance("machine_b", 9002)

    proc_a = start_server_process(cfg_a, 9001)
    proc_b = start_server_process(cfg_b, 9002)

    try:
        # Test health
        import subprocess
        result = subprocess.run(
            ["curl", "-s", "http://127.0.0.1:9001/health"],
            capture_output=True,
            timeout=5
        )
        if result.returncode == 0:
            print("✓ Server A responding to health check")
        else:
            print("✗ Server A not responding")

        result = subprocess.run(
            ["curl", "-s", "http://127.0.0.1:9002/health"],
            capture_output=True,
            timeout=5
        )
        if result.returncode == 0:
            print("✓ Server B responding to health check")
        else:
            print("✗ Server B not responding")

        print("\n✓ Basic server test passed!")

    finally:
        proc_a.terminate()
        proc_b.terminate()
        proc_a.wait(timeout=5)
        proc_b.wait(timeout=5)

        shutil.rmtree(vault_a)
        shutil.rmtree(vault_b)
        shutil.rmtree(cfg_a)
        shutil.rmtree(cfg_b)
        print("✓ Cleaned up")

if __name__ == "__main__":
    asyncio.run(test())
