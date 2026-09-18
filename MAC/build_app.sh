#!/bin/zsh
set -euo pipefail
cd "$(dirname "$0")"
python3 -m venv .build-venv
.build-venv/bin/pip install -r requirements.txt
rm -rf build dist
.build-venv/bin/pyinstaller --noconfirm --windowed --name TrollControl --osx-bundle-identifier com.trollcontrol.agent agent_mac.py
echo "Built $(pwd)/dist/TrollControl.app"
