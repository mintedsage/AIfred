#!/usr/bin/env bash
# build_appimage.sh — wraps dist/Alfred/ (from PyInstaller) into a single
# double-clickable/executable AppImage, using appimagetool.
set -euo pipefail

APP_NAME="Alfred"
VERSION="0.1.0"
DIST_DIR="dist/${APP_NAME}"
OUT_DIR="dist_installers"
APPDIR="build/linux/AppDir"

if [ ! -d "$DIST_DIR" ]; then
  echo "Error: $DIST_DIR not found. Run 'pyinstaller alfred.spec' first." >&2
  exit 1
fi

mkdir -p "$OUT_DIR"
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/bin"
cp -R "$DIST_DIR"/* "$APPDIR/usr/bin/"

cat > "$APPDIR/AppRun" <<'EOF'
#!/usr/bin/env bash
HERE="$(dirname "$(readlink -f "${0}")")"
exec "${HERE}/usr/bin/Alfred" "$@"
EOF
chmod +x "$APPDIR/AppRun"

cat > "$APPDIR/alfred.desktop" <<EOF
[Desktop Entry]
Name=Alfred
Exec=Alfred
Icon=alfred
Type=Application
Categories=Utility;
EOF

cp build/icon.png "$APPDIR/alfred.png" 2>/dev/null || echo "(no icon.png found, skipping)"

if ! command -v appimagetool >/dev/null 2>&1; then
  echo "Downloading appimagetool..."
  wget -q -O /tmp/appimagetool https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
  chmod +x /tmp/appimagetool
  APPIMAGETOOL=/tmp/appimagetool
else
  APPIMAGETOOL=appimagetool
fi

"$APPIMAGETOOL" "$APPDIR" "${OUT_DIR}/${APP_NAME}-${VERSION}-linux-x86_64.AppImage"

echo "Built ${OUT_DIR}/${APP_NAME}-${VERSION}-linux-x86_64.AppImage"
