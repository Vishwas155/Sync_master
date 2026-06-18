import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from config import get_vault_path

class VaultWatcher(FileSystemEventHandler):
    def __init__(self, on_change_callback):
        self.on_change_callback = on_change_callback
        self.debounce_timer = None

    def on_modified(self, event):
        if not event.is_directory:
            self._debounce()

    def on_created(self, event):
        if not event.is_directory:
            self._debounce()

    def _debounce(self):
        if self.debounce_timer:
            self.debounce_timer.cancel()

        self.debounce_timer = threading.Timer(3.0, self.on_change_callback)
        self.debounce_timer.start()

def start_watcher(on_change_callback):
    observer = Observer()
    vault_path = get_vault_path()

    watcher = VaultWatcher(on_change_callback)
    observer.schedule(watcher, vault_path, recursive=True)
    observer.start()

    print(f"✓ Watching vault: {vault_path}")
    return observer
