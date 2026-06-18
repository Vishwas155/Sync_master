from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QColor, QPixmap
from PySide6.QtCore import Qt, QSize

def create_tray_icon(parent_window):
    tray = QSystemTrayIcon(parent_window)

    menu = QMenu()
    menu.addAction("Show", parent_window.show)
    menu.addAction("Sync Now", lambda: parent_window.sync_requested.emit())
    menu.addSeparator()
    menu.addAction("Quit", parent_window.close)

    tray.setContextMenu(menu)

    # Create a simple green dot icon
    pixmap = QPixmap(16, 16)
    pixmap.fill(QColor("green"))
    tray.setIcon(QIcon(pixmap))

    tray.show()
    return tray

def update_tray_icon(tray, status: str):
    color_map = {
        "idle": "green",
        "syncing": "orange",
        "error": "red"
    }
    color = color_map.get(status, "gray")

    pixmap = QPixmap(16, 16)
    pixmap.fill(QColor(color))
    tray.setIcon(QIcon(pixmap))
