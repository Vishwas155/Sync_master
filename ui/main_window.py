from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QListWidget, QListWidgetItem, QTextEdit
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QIcon, QColor
from config import get_vault_path, get_device_name
from discovery import get_online_peers

class MainWindow(QMainWindow):
    sync_requested = Signal()
    activity_updated = Signal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("ObsSync")
        self.setGeometry(100, 100, 500, 600)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout()

        # Vault info
        vault_label = QLabel(f"Vault: {get_vault_path()}")
        layout.addWidget(vault_label)

        status_label = QLabel("Status: ● Watching")
        self.status_label = status_label
        layout.addWidget(status_label)

        # Peers list
        peers_title = QLabel("Peers")
        layout.addWidget(peers_title)

        self.peers_list = QListWidget()
        layout.addWidget(self.peers_list)

        # Activity feed
        activity_title = QLabel("Activity")
        layout.addWidget(activity_title)

        self.activity_text = QTextEdit()
        self.activity_text.setReadOnly(True)
        layout.addWidget(self.activity_text)

        # Sync button
        sync_button = QPushButton("Sync Now")
        sync_button.clicked.connect(self.on_sync_click)
        layout.addWidget(sync_button)

        central.setLayout(layout)
        self.update_peers_list()

        # Connect signal for thread-safe UI updates
        self.activity_updated.connect(self._update_activity_safe)

    def on_sync_click(self):
        self.sync_requested.emit()
        self.add_activity("Sync initiated...")

    def update_peers_list(self):
        self.peers_list.clear()
        peers = get_online_peers()

        if not peers:
            item = QListWidgetItem("No peers discovered")
            self.peers_list.addItem(item)
        else:
            for peer in peers:
                ip = peer.get("ip", "unknown")
                port = peer.get("port", "")
                text = f"● {ip}:{port}"
                item = QListWidgetItem(text)
                self.peers_list.addItem(item)

    def add_activity(self, message: str):
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        text = f"{timestamp}  {message}"
        self.activity_updated.emit(text)

    def _update_activity_safe(self, message: str):
        current = self.activity_text.toPlainText()
        self.activity_text.setText(f"{message}\n{current}")

    def update_status(self, syncing: bool):
        if syncing:
            self.status_label.setText("Status: ↻ Syncing...")
        else:
            self.status_label.setText("Status: ● Watching")
