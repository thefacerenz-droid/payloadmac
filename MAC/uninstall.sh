#!/bin/zsh
set -euo pipefail
PLIST="$HOME/Library/LaunchAgents/com.trollcontrol.agent.plist"; APP="$HOME/Applications/TrollControl.app"
echo "This unloads Troll Control and removes $PLIST, $APP, and its local device ID."
read "reply?Type UNINSTALL to continue: "; [[ "$reply" == UNINSTALL ]] || { echo "Cancelled."; exit 0; }
[[ -f "$PLIST" ]] && launchctl bootout "gui/$(id -u)" "$PLIST" 2>/dev/null || true
rm -f "$PLIST" "$HOME/.trollcontrol-device-id"
rm -rf "$APP"
echo "Troll Control removed. Also use dashboard Unpair to revoke its server record."
