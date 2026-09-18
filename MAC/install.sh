#!/bin/zsh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"; APP="$ROOT/dist/TrollControl.app"; DEST="$HOME/Applications/TrollControl.app"; PLIST="$HOME/Library/LaunchAgents/com.trollcontrol.agent.plist"
echo "Troll Control installs a visible authorized remote-control app into $DEST."
echo "It connects outbound to the configured server and permits only documented allowlisted controls."
echo "It creates $PLIST so it starts when you log in. Remove it with uninstall.sh."
read "reply?Type INSTALL to continue: "; [[ "$reply" == INSTALL ]] || { echo "Cancelled."; exit 0; }
[[ -d "$APP" ]] || { echo "Build TrollControl.app first with ./build_app.sh"; exit 1; }
read "server?Backend WebSocket URL (for example wss://backend.example.com): "
read -s "agent_token?Agent token (the configured ADMIN_TOKEN): "; echo
[[ "$server" == wss://* || "$server" == ws://* ]] || { echo "Use a ws:// or wss:// URL."; exit 1; }
[[ -n "$agent_token" ]] || { echo "Agent token is required."; exit 1; }
mkdir -p "$HOME/Applications" "$HOME/Library/LaunchAgents"
rm -rf "$DEST"; cp -R "$APP" "$DEST"
cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd"><plist version="1.0"><dict><key>Label</key><string>com.trollcontrol.agent</string><key>ProgramArguments</key><array><string>$DEST/Contents/MacOS/TrollControl</string></array><key>EnvironmentVariables</key><dict><key>TROLL_CONTROL_SERVER</key><string>$server</string><key>TROLL_CONTROL_AGENT_TOKEN</key><string>$agent_token</string></dict><key>RunAtLoad</key><true/><key>KeepAlive</key><true/><key>StandardOutPath</key><string>$HOME/Library/Logs/TrollControl.log</string><key>StandardErrorPath</key><string>$HOME/Library/Logs/TrollControl.log</string></dict></plist>
EOF
launchctl bootout "gui/$(id -u)" "$PLIST" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST"
open "$DEST"
echo "Installed. To stop/uninstall, run $ROOT/uninstall.sh"
