#!/usr/bin/env python3
"""
Headless sync server for Android (Termux) or CLI-only deployments.
No UI, runs in background, auto-syncs on interval.
"""
import asyncio
import time
from threading import Thread
from server import run_server
from db import init_db
from discovery import advertise_service, discover_peers, get_online_peers
from sync_engine import sync_with_peer
from config import get_device_name, get_auto_sync

def log(msg: str):
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] {msg}")

async def auto_sync_loop():
    """Periodically sync with all peers."""
    log("Auto-sync loop started")
    while True:
        await asyncio.sleep(60)  # Check every 60s
        if not get_auto_sync():
            continue

        peers = get_online_peers()
        if not peers:
            continue

        log(f"Auto-sync: {len(peers)} peer(s) available")
        for peer in peers:
            try:
                result = await sync_with_peer(peer["ip"], peer["port"])
                if result["status"] == "success":
                    log(f"✓ Synced {result['synced_count']} files with {peer['ip']}")
                else:
                    log(f"✗ {result['message']}")
            except Exception as e:
                log(f"✗ Sync error: {e}")

def run_server_thread():
    """Run FastAPI server in background thread."""
    log("Starting FastAPI server")
    run_server()

def main():
    log(f"ObsSync Headless (device: {get_device_name()})")
    log("Initializing database...")
    init_db()

    log("Starting peer discovery...")
    advertise_service()
    discover_peers()

    # Start server in background
    server_thread = Thread(target=run_server_thread, daemon=True)
    server_thread.start()
    time.sleep(1)

    log("Server ready. Starting sync loop...")
    try:
        asyncio.run(auto_sync_loop())
    except KeyboardInterrupt:
        log("Shutdown requested")
    except Exception as e:
        log(f"Error: {e}")

if __name__ == "__main__":
    main()
