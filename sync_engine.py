import hashlib
import time
from pathlib import Path
from typing import Optional
import aiohttp
import aiofiles
from config import get_vault_path
from db import update_file_info

async def compute_file_hash(file_path: Path) -> str:
    hasher = hashlib.sha256()
    async with aiofiles.open(file_path, "rb") as f:
        while True:
            chunk = await f.read(8192)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()

async def build_local_manifest() -> list[dict]:
    vault_path = get_vault_path()
    manifest = []

    for file_path in vault_path.rglob("*"):
        if file_path.is_file() and not file_path.name.startswith("."):
            rel_path = file_path.relative_to(vault_path).as_posix()
            file_hash = await compute_file_hash(file_path)
            mtime = file_path.stat().st_mtime

            manifest.append({
                "path": rel_path,
                "hash": file_hash,
                "mtime": mtime
            })

    return manifest

async def get_remote_manifest(peer_ip: str, peer_port: int) -> Optional[list[dict]]:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"http://{peer_ip}:{peer_port}/manifest", timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    return await resp.json()
    except Exception as e:
        print(f"Failed to fetch remote manifest from {peer_ip}:{peer_port}: {e}")
    return None

async def pull_file(peer_ip: str, peer_port: int, file_path: str) -> Optional[bytes]:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"http://{peer_ip}:{peer_port}/file?path={file_path}", timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    return await resp.read()
    except Exception as e:
        print(f"Failed to pull {file_path} from {peer_ip}:{peer_port}: {e}")
    return None

async def push_file(peer_ip: str, peer_port: int, file_path: str, content: bytes, mtime: float) -> bool:
    try:
        async with aiohttp.ClientSession() as session:
            data = aiohttp.FormData()
            data.add_field("path", file_path)
            data.add_field("content", content)
            data.add_field("mtime", str(mtime))

            async with session.post(f"http://{peer_ip}:{peer_port}/push", data=data, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                return resp.status == 200
    except Exception as e:
        print(f"Failed to push {file_path} to {peer_ip}:{peer_port}: {e}")
    return False

async def sync_with_peer(peer_ip: str, peer_port: int) -> dict:
    local_manifest = await build_local_manifest()
    remote_manifest = await get_remote_manifest(peer_ip, peer_port)

    if remote_manifest is None:
        return {"status": "error", "message": f"Could not reach {peer_ip}:{peer_port}"}

    local_map = {f["path"]: f for f in local_manifest}
    remote_map = {f["path"]: f for f in remote_manifest}

    synced_files = []
    vault_path = get_vault_path()

    # Files only local → push
    for path in local_map:
        if path not in remote_map:
            file_path = vault_path / path
            async with aiofiles.open(file_path, "rb") as f:
                content = await f.read()
            mtime = file_path.stat().st_mtime
            success = await push_file(peer_ip, peer_port, path, content, mtime)
            if success:
                synced_files.append((path, "push"))
            print(f"{'✓' if success else '✗'} Push: {path}")

    # Files only remote → pull
    for path in remote_map:
        if path not in local_map:
            content = await pull_file(peer_ip, peer_port, path)
            if content:
                file_path = vault_path / path
                file_path.parent.mkdir(parents=True, exist_ok=True)
                async with aiofiles.open(file_path, "wb") as f:
                    await f.write(content)
                mtime = remote_map[path]["mtime"]
                update_file_info(path, remote_map[path]["hash"], mtime, time.time())
                synced_files.append((path, "pull"))
                print(f"✓ Pull: {path}")

    # Both exist → compare hash
    for path in local_map:
        if path in remote_map:
            if local_map[path]["hash"] != remote_map[path]["hash"]:
                # Conflict: latest mtime wins
                if local_map[path]["mtime"] > remote_map[path]["mtime"]:
                    # Local is newer → push
                    file_path = vault_path / path
                    async with aiofiles.open(file_path, "rb") as f:
                        content = await f.read()
                    mtime = file_path.stat().st_mtime
                    success = await push_file(peer_ip, peer_port, path, content, mtime)
                    if success:
                        synced_files.append((path, "push-conflict"))
                    print(f"{'✓' if success else '✗'} Conflict (local newer): {path}")
                else:
                    # Remote is newer → pull
                    content = await pull_file(peer_ip, peer_port, path)
                    if content:
                        file_path = vault_path / path
                        file_path.parent.mkdir(parents=True, exist_ok=True)
                        async with aiofiles.open(file_path, "wb") as f:
                            await f.write(content)
                        mtime = remote_map[path]["mtime"]
                        update_file_info(path, remote_map[path]["hash"], mtime, time.time())
                        synced_files.append((path, "pull-conflict"))
                        print(f"✓ Conflict (remote newer): {path}")

    return {
        "status": "success",
        "synced_count": len(synced_files),
        "synced_files": synced_files,
        "peer": f"{peer_ip}:{peer_port}"
    }
