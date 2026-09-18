import asyncio, json, os, secrets, time
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, File, Header, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

load_dotenv()
TOKEN = os.environ.get("ADMIN_TOKEN", "")
PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "").rstrip("/")
if not TOKEN:
    raise RuntimeError("ADMIN_TOKEN must be set")
UPLOADS = Path("uploads"); UPLOADS.mkdir(exist_ok=True)
ALLOWED = {"ping", "wallpaper", "sound", "calculator", "message", "bluetooth", "shutdown"}
devices: dict[str, dict[str, Any]] = {}
app = FastAPI(title="Troll Control")
origins = [x.strip() for x in os.environ.get("CORS_ORIGINS", "*").split(",")]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=False, allow_methods=["*"], allow_headers=["*"])
app.mount("/uploads", StaticFiles(directory=UPLOADS), name="uploads")

def auth(authorization: str | None):
    if not authorization or not secrets.compare_digest(authorization.removeprefix("Bearer "), TOKEN):
        raise HTTPException(401, "Unauthorized")

def public(d: dict[str, Any]):
    return {k: d.get(k) for k in ("id", "hostname", "os", "version", "online", "authorized", "last_seen")}

@app.get("/")
def root(): return {"name": "Troll Control", "status": "ok"}
@app.get("/health")
def health(): return {"ok": True}
@app.get("/api/devices")
def list_devices(authorization: str | None = Header(None)):
    auth(authorization); return [public(d) for d in devices.values()]

async def send_command(device_id: str, command: str, payload: dict[str, Any] | None = None):
    if command not in ALLOWED: raise HTTPException(400, "Command is not allowlisted")
    d = devices.get(device_id)
    if not d or not d["online"]: raise HTTPException(404, "Device is offline or unknown")
    request_id = secrets.token_urlsafe(12); future = asyncio.get_running_loop().create_future()
    d["pending"][request_id] = future
    try:
        await d["ws"].send_json({"type":"command", "id":request_id, "command":command, "payload":payload or {}})
        return await asyncio.wait_for(future, timeout=40)
    except asyncio.TimeoutError: raise HTTPException(504, "Agent did not respond")
    finally: d["pending"].pop(request_id, None)

@app.post("/api/devices/{device_id}/command/{command}")
async def command(device_id: str, command: str, authorization: str | None = Header(None)):
    auth(authorization); return await send_command(device_id, command)
@app.post("/api/devices/{device_id}/wallpaper")
async def wallpaper(device_id: str, body: dict[str, str], authorization: str | None = Header(None)):
    auth(authorization)
    if not body.get("url"): raise HTTPException(400, "A wallpaper URL is required")
    return await send_command(device_id, "wallpaper", {"url": body["url"]})
@app.post("/api/devices/{device_id}/unpair")
async def unpair(device_id: str, authorization: str | None = Header(None)):
    auth(authorization); d = devices.pop(device_id, None)
    if not d: raise HTTPException(404, "Unknown device")
    await d["ws"].close(code=4001); return {"ok": True}
@app.post("/api/wallpaper")
async def upload_wallpaper(image: UploadFile = File(...), authorization: str | None = Header(None)):
    auth(authorization)
    if not image.content_type or not image.content_type.startswith("image/"): raise HTTPException(400, "Image files only")
    suffix = Path(image.filename or "image").suffix.lower() or ".jpg"; name = secrets.token_urlsafe(16) + suffix
    content = await image.read()
    if len(content) > 15 * 1024 * 1024: raise HTTPException(413, "Image exceeds 15 MB")
    (UPLOADS / name).write_bytes(content)
    if not PUBLIC_BASE_URL: raise HTTPException(500, "PUBLIC_BASE_URL is not configured")
    return {"url": f"{PUBLIC_BASE_URL}/uploads/{name}"}

@app.websocket("/agent")
async def agent(ws: WebSocket):
    if not secrets.compare_digest(ws.query_params.get("token", ""), TOKEN): await ws.close(code=4401); return
    await ws.accept(); device_id = None
    try:
        while True:
            msg = await ws.receive_json(); kind = msg.get("type")
            if kind == "hello":
                device_id = msg.get("id") or secrets.token_urlsafe(12)
                devices[device_id] = {"id":device_id, "hostname":msg.get("hostname", "Unknown Mac"), "os":msg.get("os", "macOS"), "version":msg.get("version", ""), "online":True, "authorized":True, "last_seen":time.time(), "ws":ws, "pending":{}}
                await ws.send_json({"type":"registered", "id":device_id})
            elif device_id and kind == "heartbeat": devices[device_id]["last_seen"] = time.time()
            elif device_id and kind == "result":
                d = devices[device_id]; d["last_seen"] = time.time(); f = d["pending"].get(msg.get("id"))
                if f and not f.done(): f.set_result({"ok": bool(msg.get("ok")), "message": msg.get("message", "")})
    except WebSocketDisconnect: pass
    finally:
        if device_id in devices:
            devices[device_id]["online"] = False; devices[device_id]["last_seen"] = time.time()
