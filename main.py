import sys
import asyncio
from threading import Thread
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
from ui.tray import create_tray_icon, update_tray_icon
from server import run_server
from config import get_auto_sync
from db import init_db
from discovery import advertise_service, discover_peers, get_online_peers
from sync_engine import sync_with_peer

class SyncLoop:
    def __init__(self, main_window):
        self.main_window = main_window
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    async def auto_sync_task(self):
        while True:
            await asyncio.sleep(30)
            peers = get_online_peers()
            if peers and get_auto_sync():
                for peer in peers:
                    result = await sync_with_peer(peer["ip"], peer["port"])
                    if result["status"] == "success":
                        self.main_window.add_activity(f"Synced {result['synced_count']} files with {result['peer']}")

    async def manual_sync_task(self):
        peers = get_online_peers()
        if not peers:
            self.main_window.add_activity("No peers available to sync with")
            return

        update_tray_icon(self.main_window.tray, "syncing")
        self.main_window.update_status(True)

        for peer in peers:
            result = await sync_with_peer(peer["ip"], peer["port"])
            if result["status"] == "success":
                self.main_window.add_activity(f"✓ Synced {result['synced_count']} files → {result['peer']}")
            else:
                self.main_window.add_activity(f"✗ {result['message']}")

        update_tray_icon(self.main_window.tray, "idle")
        self.main_window.update_status(False)

    def on_sync_requested(self):
        asyncio.run_coroutine_threadsafe(self.manual_sync_task(), self.loop)

    def run(self):
        self.main_window.sync_requested.connect(self.on_sync_requested)
        self.loop.run_until_complete(self.auto_sync_task())

def main():
    init_db()

    app = QApplication(sys.argv)

    # Start server in thread
    server_thread = Thread(target=run_server, daemon=True)
    server_thread.start()
    print("✓ Server started")

    # Start discovery
    advertise_service()
    discover_peers()

    # Create UI
    main_window = MainWindow()
    main_window.tray = create_tray_icon(main_window)
    main_window.show()

    # Start sync loop in thread
    sync_loop = SyncLoop(main_window)
    sync_thread = Thread(target=sync_loop.run, daemon=True)
    sync_thread.start()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
