# Troll Control

Troll Control is an **authorized-use** remote-control project for Macs you own or administer. It has a static iPad-friendly dashboard, a persistent FastAPI/WebSocket backend, and a visible macOS agent. It is deliberately limited to wallpaper, notification sound, Calculator, a message, Bluetooth settings, and locally-confirmed shutdown. It has no shell, file, screen, credential, or input-control features.

## Quick start

1. Copy `server/.env.example` to `server/.env`, set a long `ADMIN_TOKEN`, and set `PUBLIC_BASE_URL` to the public HTTPS URL of the backend.
2. Run the backend: `cd server; python -m venv .venv; .venv\\Scripts\\pip install -r requirements.txt; uvicorn server:app --host 0.0.0.0 --port 8000` (on macOS/Linux, use `.venv/bin/pip`).
3. Set `API_BASE` in `dashboard/app.js` to the backend URL and deploy `dashboard/` as a Vercel static project.
4. Set `TROLL_CONTROL_SERVER` and `TROLL_CONTROL_AGENT_TOKEN` when building/installing the Mac app. The agent token is the same `ADMIN_TOKEN` in this initial single-admin version.

## Deployment

Use a host that supports long-lived WebSockets (a VM, Render, Railway, Fly.io, etc.); Vercel hosts only `dashboard/`. Configure `ADMIN_TOKEN`, `PUBLIC_BASE_URL`, and optionally `CORS_ORIGINS` on that host, then run `uvicorn server:app --host 0.0.0.0 --port $PORT`. Terminate TLS at the host/proxy so agents use `wss://`.

For Vercel, import this repository, select `dashboard` as the root directory, and deploy. Edit `dashboard/app.js` before deployment (or replace it during CI) with the real backend URL. Enter the admin token in the dashboard when prompted; it is kept only in browser session storage.

## Mac app and release

On a Mac: `cd MAC && chmod +x build_app.sh package_release.sh install.sh uninstall.sh && ./build_app.sh && ./package_release.sh`. This creates `MAC/dist/TrollControl.app` and `MAC/dist/TrollControl-mac.zip`. Create a GitHub Release/tag and upload that ZIP.

If you do not own a Mac, push this repository to GitHub and create a tag beginning with `v` (for example `v1.0.0`). The included GitHub Actions macOS workflow builds the ZIP on GitHub and attaches it to the new Release automatically. The unsigned app may still require the authorized Mac owner to approve macOS security prompts.

For distribution outside your own Macs, sign with a Developer ID certificate and notarize using `codesign --deep --force --options runtime --sign 'Developer ID Application: …' dist/TrollControl.app` and `xcrun notarytool submit … --wait`, then staple it. Test the signed build on a clean Mac.

## Installation, removal, and permissions

Open the released installer visibly or run `MAC/install.sh`. It describes the app, asks for confirmation, copies it to `~/Applications`, and creates a named `LaunchAgent` so it can reconnect after login. The app is visible in Activity Monitor. Run `MAC/uninstall.sh` to unload the agent and remove all files. The device can also be revoked with **Unpair** in the dashboard.

macOS may request Automation permission for wallpaper or Bluetooth settings, and notification permission for messages. Shutdown always presents a local GUI confirmation; canceling it reports a failure to the dashboard.

## Troubleshooting

* `/health` should return `{"ok":true}`; use it before connecting an agent.
* A dashboard “Unauthorized” error means its token differs from `ADMIN_TOKEN`.
* Ensure `PUBLIC_BASE_URL` is publicly reachable HTTPS, otherwise wallpaper URLs will not reach the Mac.
* Inspect `~/Library/Logs/TrollControl.log` and reload `~/Library/LaunchAgents/com.trollcontrol.agent.plist` after changing agent configuration.
* An offline device has disconnected; the agent reconnects automatically while it is running.

See `server/README.md` and `T-EMBED/INSTALL-MAC.txt` for exact setup details.
