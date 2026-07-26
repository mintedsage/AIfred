#!/usr/bin/env bash
# build_dmg.sh — wraps dist/Alfred.app (from PyInstaller's BUNDLE step) into
# a real double-click .dmg installer, using macOS's built-in hdiutil.
# Run this on macOS (or in the macos-latest GitHub Actions runner).
set -euo pipefail

APP_NAME="Alfred"
VERSION="0.1.0"
DIST_APP="dist/${APP_NAME}.app"
OUT_DIR="dist_installers"
DMG_PATH="${OUT_DIR}/${APP_NAME}-${VERSION}-mac.dmg"
STAGING_DIR="dist/dmg_staging"

if [ ! -d "$DIST_APP" ]; then
  echo "Error: $DIST_APP not found. Run 'pyinstaller alfred.spec' first." >&2
  exit 1
fi

mkdir -p "$OUT_DIR"
rm -rf "$STAGING_DIR"
mkdir -p "$STAGING_DIR"

cp -R "$DIST_APP" "$STAGING_DIR/"
ln -s /Applications "$STAGING_DIR/Applications"

rm -f "$DMG_PATH"
hdiutil create -volname "$APP_NAME" -srcfolder "$STAGING_DIR" -ov -format UDZO "$DMG_PATH"

echo "Built $DMG_PATH"
echo "Note: this build is not code-signed or notarized. On first launch,"
echo "macOS Gatekeeper will warn the user; they'll need to right-click ->"
echo "Open once. Proper notarization requires a paid Apple Developer account."
