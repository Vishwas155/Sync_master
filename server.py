from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse
import time
from pathlib import Path
import aiofiles
from config import get_vault_path, get_port, get_device_name
from db import get_manifest, update_file_info
from sync_engine import build_local_manifest

app = FastAPI()

@app.get("/manifest")
async def get_manifest_endpoint():
    manifest = await build_local_manifest()
    return manifest

@app.get("/file")
async def get_file(path: str):
    vault_path = get_vault_path()
    file_path = vault_path / path

    # Prevent path traversal
    try:
        file_path = file_path.resolve()
        vault_path = vault_path.resolve()
        if not str(file_path).startswith(str(vault_path)):
            return JSONResponse({"error": "Access denied"}, status_code=403)
    except:
        return JSONResponse({"error": "Invalid path"}, status_code=400)

    if not file_path.exists() or not file_path.is_file():
        return JSONResponse({"error": "File not found"}, status_code=404)

    return FileResponse(file_path)

@app.post("/push")
async def push_file(path: str = Form(...), content: UploadFile = File(...), mtime: str = Form(...)):
    vault_path = get_vault_path()
    file_path = vault_path / path

    # Prevent path traversal
    try:
        file_path = file_path.resolve()
        vault_path = vault_path.resolve()
        if not str(file_path).startswith(str(vault_path)):
            return JSONResponse({"error": "Access denied"}, status_code=403)
    except:
        return JSONResponse({"error": "Invalid path"}, status_code=400)

    file_path.parent.mkdir(parents=True, exist_ok=True)

    contents = await content.read()
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(contents)

    mtime_float = float(mtime)
    file_path.stat()

    import hashlib
    hash_obj = hashlib.sha256()
    hash_obj.update(contents)
    file_hash = hash_obj.hexdigest()

    update_file_info(path, file_hash, mtime_float, time.time())

    return {"status": "ok", "path": path}

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "device": get_device_name(),
        "port": get_port()
    }

def run_server():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=get_port(), log_level="error")
