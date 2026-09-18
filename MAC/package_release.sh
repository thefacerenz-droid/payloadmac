#!/bin/zsh
# Run after ./build_app.sh on a Mac. Creates the exact GitHub Release upload.
set -euo pipefail
cd "$(dirname "$0")"
[[ -d dist/TrollControl.app ]] || { echo "Run ./build_app.sh first."; exit 1; }
rm -rf release/TrollControl-mac
mkdir -p release/TrollControl-mac/MAC/dist
cp -R dist/TrollControl.app release/TrollControl-mac/MAC/dist/
cp install.sh uninstall.sh release/TrollControl-mac/MAC/
cp ../README.md release/TrollControl-mac/
chmod +x release/TrollControl-mac/MAC/install.sh release/TrollControl-mac/MAC/uninstall.sh
rm -f dist/TrollControl-mac.zip
ditto -c -k --sequesterRsrc --keepParent release/TrollControl-mac dist/TrollControl-mac.zip
echo "Upload $(pwd)/dist/TrollControl-mac.zip to the GitHub Release."
