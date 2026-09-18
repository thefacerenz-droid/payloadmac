import asyncio, json, os, platform, subprocess, sys, tempfile, urllib.request, uuid
from pathlib import Path
import websockets

SERVER=os.environ.get('TROLL_CONTROL_SERVER','wss://YOUR-SERVER-DOMAIN').rstrip('/')
TOKEN=os.environ.get('TROLL_CONTROL_AGENT_TOKEN','')
DEVICE_FILE=Path.home()/'.trollcontrol-device-id'
DEVICE_ID=DEVICE_FILE.read_text().strip() if DEVICE_FILE.exists() else str(uuid.uuid4())
DEVICE_FILE.write_text(DEVICE_ID)
def run(args): subprocess.run(args, check=True)
def osa(script): run(['osascript','-e',script])
def action(command,payload):
    if command=='ping': return 'Pong'
    if command=='sound': run(['/usr/bin/afplay','/System/Library/Sounds/Glass.aiff']); return 'Notification sound played'
    if command=='calculator': run(['/usr/bin/open','-a','Calculator']); return 'Calculator opened'
    if command=='message': osa('display notification "Hello from Troll Control!" with title "Troll Control"'); return 'Message displayed'
    if command=='bluetooth': run(['/usr/bin/open','x-apple.systempreferences:com.apple.BluetoothSettings']); return 'Bluetooth settings opened'
    if command=='wallpaper':
        url=payload.get('url','')
        if not url.startswith('https://'): raise ValueError('Wallpaper URL must use HTTPS')
        target=Path(tempfile.gettempdir())/'trollcontrol-wallpaper'+Path(url).suffix
        urllib.request.urlretrieve(url,target)
        osa(f'tell application "System Events" to tell every desktop to set picture to POSIX file "{target}"')
        return 'Wallpaper applied'
    if command=='shutdown':
        osa('display dialog "Troll Control requests shutdown. Shut down this Mac now?" buttons {"Cancel", "Shut Down"} default button "Cancel" with icon caution')
        run(['/sbin/shutdown','-h','now']); return 'Shutdown confirmed locally'
    raise ValueError('Command is not allowlisted')
async def heartbeat(ws):
    while True: await asyncio.sleep(20); await ws.send(json.dumps({'type':'heartbeat'}))
async def connect():
    if not TOKEN: raise RuntimeError('TROLL_CONTROL_AGENT_TOKEN is required')
    url=f'{SERVER}/agent?token={TOKEN}'
    async with websockets.connect(url, ping_interval=20, ping_timeout=20) as ws:
        await ws.send(json.dumps({'type':'hello','id':DEVICE_ID,'hostname':platform.node(),'os':'macOS','version':platform.mac_ver()[0]}))
        hb=asyncio.create_task(heartbeat(ws))
        try:
            async for raw in ws:
                msg=json.loads(raw)
                if msg.get('type')!='command': continue
                try: message=action(msg['command'],msg.get('payload',{})); out={'ok':True,'message':message}
                except Exception as e: out={'ok':False,'message':str(e)}
                await ws.send(json.dumps({'type':'result','id':msg.get('id'),**out}))
        finally: hb.cancel()
async def main():
    while True:
        try: await connect()
        except Exception as e: print(f'Connection error: {e}',flush=True); await asyncio.sleep(10)
if __name__=='__main__': asyncio.run(main())
