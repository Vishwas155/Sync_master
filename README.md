# ObsSync — Local Network Obsidian Vault Sync

Sync your Obsidian vaults between macOS and Windows devices on the same Wi-Fi network. Zero cloud, zero Git. Just local peer-to-peer sync over LAN.

## Features

✓ **Auto-discover peers** — mDNS broadcasts find other ObsSync instances automatically  
✓ **Manual + auto sync** — Click "Sync Now" or auto-sync on file change  
✓ **Conflict resolution** — Latest file timestamp wins (simple, works for personal use)  
✓ **Efficient transfer** — Only changed files are synced, hash-based dedup  
✓ **Tray integration** — Runs in system tray, doesn't clutter your screen  

## Architecture

```
Device A (macOS)                Device B (Windows)
├─ PySide6 Desktop UI          ├─ PySide6 Desktop UI
├─ FastAPI Server :8765        ├─ FastAPI Server :8765
├─ watchdog (file monitor)     ├─ watchdog (file monitor)
├─ zeroconf (mDNS discovery)   ├─ zeroconf (mDNS discovery)
└─ SQLite state DB             └─ SQLite state DB

         LAN (Wi-Fi)
         mDNS broadcast + TCP file transfer
```

## Setup

### Requirements
- macOS 10.15+ or Windows 10+
- Python 3.9+
- Same Wi-Fi network

### Install

```bash
git clone <repo>
cd obsync
python3 -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
```

### Configuration (Before First Run)

First, decide where your Obsidian vault is located:

**macOS/Linux:**

```bash
~/Documents/Obsidian      # Default location
~/Vaults/MyVault          # Or anywhere else
/mnt/backup/vault         # Or external drive
```

**Windows:**

```
C:\Users\YourName\Documents\Obsidian
C:\Vaults\MyVault
D:\backup\vault
```

### Run

```bash
python3 main.py
```

On first run, app creates `~/.obsync/config.json` with defaults:

```json
{
  "vault_path": "/Users/vishwas/Documents/Obsidian",
  "port": 8765,
  "device_name": "vishwass-MacBook-Air",
  "auto_sync": true
}
```

**Customize vault path:**

Edit `~/.obsync/config.json` before running again:

```json
{
  "vault_path": "/Users/vishwas/Vaults/MyPersonalVault",
  "port": 8765,
  "device_name": "MyMac",
  "auto_sync": true
}
```

Then restart app:

```bash
python3 main.py
```

**Config fields:**

- `vault_path` — Full path to Obsidian vault (must exist)
- `port` — Server port (8765 default, change if conflict)
- `device_name` — Name shown to peers (e.g., "Laptop", "Desktop")
- `auto_sync` — Auto-sync on file change (true/false)

## How It Works

### 1. Discovery
Each instance broadcasts a mDNS service (`_obsync._tcp.local.`). Peers auto-discover without manual setup.

### 2. Manifest Exchange
When syncing, machines exchange file manifests:
```json
[
  {"path": "daily.md", "hash": "abc123...", "mtime": 1718630000},
  {"path": "projects/obsync.md", "hash": "def456...", "mtime": 1718631000}
]
```

### 3. Diff & Transfer
Compare local vs. remote manifests:
- **Only local** → push to peer
- **Only remote** → pull from peer
- **Both exist, different hash** → latest mtime wins

### 4. File Transfer
- `GET /file?path=notes/daily.md` — download file bytes
- `POST /push` — upload file with mtime

### Conflict Resolution

If both machines edit the same file:
```
Machine A: daily.md (mtime: 1718630100)
Machine B: daily.md (mtime: 1718630150)  ← newer
```
Result: B's version wins on both machines.

For personal single-user workflows, this is sufficient. If you edit the same file on multiple machines, the latest edit wins.

## Development

### Run Tests
```bash
python3 test_sync.py
```

Starts two isolated server instances and verifies:
- Health checks pass
- Servers respond independently
- Config isolation works

### Project Structure
```
obsync/
├── main.py              # Entry point: UI + server + discovery
├── server.py            # FastAPI endpoints
├── sync_engine.py       # Diff logic + file transfer
├── db.py                # SQLite manifest storage
├── config.py            # Settings (vault, port, device name)
├── discovery.py         # mDNS peer discovery
├── file_watcher.py      # watchdog integration
└── ui/
    ├── main_window.py   # PySide6 UI
    └── tray.py          # System tray icon
```

## Limitations (MVP)

- No end-to-end encryption (LAN-only, trusted network assumed)
- No authentication (LAN-only, personal use)
- No partial file sync (full files only)
- No version history (latest wins, no rollback)

## Phase 2 (Future)

- [ ] Android support (Flutter app)
- [ ] iOS support (if Android goes well)
- [ ] Encryption option
- [ ] Selective sync (only sync certain folders)
- [ ] Detailed sync history viewer
- [ ] Multi-user support with permissions

## Troubleshooting

### "No peers discovered"
- Verify both machines on same Wi-Fi
- Check firewall allows port 8765 (or custom port)
- Try restarting app on both machines

### Files not syncing
- Check vault paths exist and are readable
- Verify no files are currently open in Obsidian (some editors lock files)
- Check `~/.obsync/sync.db` not corrupted (delete to reset)

### Port already in use
Change `port` in `~/.obsync/config.json` and restart.

## License

MIT
