import sqlite3
import os
from pathlib import Path
from typing import Optional

DB_PATH = Path(os.environ.get("OBSYNC_HOME", Path.home() / ".obsync")) / "sync.db"

def init_db():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS file_manifest (
        id INTEGER PRIMARY KEY,
        file_path TEXT NOT NULL UNIQUE,
        hash TEXT NOT NULL,
        mtime REAL NOT NULL,
        last_synced REAL NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS peer_state (
        id INTEGER PRIMARY KEY,
        device_name TEXT NOT NULL UNIQUE,
        last_seen REAL,
        ip_address TEXT,
        port INTEGER
    )
    """)

    conn.commit()
    conn.close()

def get_file_info(file_path: str) -> Optional[dict]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT hash, mtime, last_synced FROM file_manifest WHERE file_path = ?", (file_path,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return {"hash": row[0], "mtime": row[1], "last_synced": row[2]}
    return None

def update_file_info(file_path: str, hash: str, mtime: float, last_synced: float):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    INSERT OR REPLACE INTO file_manifest (file_path, hash, mtime, last_synced)
    VALUES (?, ?, ?, ?)
    """, (file_path, hash, mtime, last_synced))
    conn.commit()
    conn.close()

def get_manifest() -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT file_path, hash, mtime FROM file_manifest")
    rows = cursor.fetchall()
    conn.close()

    return [{"path": r[0], "hash": r[1], "mtime": r[2]} for r in rows]

def update_peer(device_name: str, ip_address: str, port: int, last_seen: float):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    INSERT OR REPLACE INTO peer_state (device_name, ip_address, port, last_seen)
    VALUES (?, ?, ?, ?)
    """, (device_name, ip_address, port, last_seen))
    conn.commit()
    conn.close()

def get_peer(device_name: str) -> Optional[dict]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT ip_address, port, last_seen FROM peer_state WHERE device_name = ?", (device_name,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return {"ip": row[0], "port": row[1], "last_seen": row[2]}
    return None

def get_all_peers() -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT device_name, ip_address, port, last_seen FROM peer_state")
    rows = cursor.fetchall()
    conn.close()

    return [{"device": r[0], "ip": r[1], "port": r[2], "last_seen": r[3]} for r in rows]
