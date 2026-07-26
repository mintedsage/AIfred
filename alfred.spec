# alfred.spec — PyInstaller build spec.
#
# Builds Alfred into a standalone onedir app that bundles a Python runtime,
# so end users don't need Python or pip installed. Ollama itself is NOT
# bundled (it's a separate system service with its own installer) — the
# platform installers below prompt the user to install it if missing.
#
# Usage: pyinstaller alfred.spec  (run per-OS; see .github/workflows/build.yml
# for how this is done automatically on Windows/macOS/Linux via CI.)

import os
import sys
from PyInstaller.utils.hooks import collect_all

block_cipher = None

def _icon_or_none(path):
    return path if os.path.exists(path) else None


datas = [("ui/static", "ui/static")]
binaries = []
hiddenimports = [
    "ollama",
    "uvicorn.logging",
    "uvicorn.loops.auto",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan.on",
]

# Heavy ML/voice libs ship their own data files (tokenizer configs, model
# metadata, native extensions) that PyInstaller won't find automatically.
for pkg in ["sentence_transformers", "huggingface_hub", "faster_whisper", "ctranslate2", "tokenizers", "pyttsx3"]:
    d, b, h = collect_all(pkg)
    datas += d
    binaries += b
    hiddenimports += h

# pywebview's GUI backend is platform-specific.
if sys.platform.startswith("win"):
    hiddenimports += ["clr", "webview.platforms.winforms", "webview.platforms.edgechromium"]
elif sys.platform == "darwin":
    hiddenimports += ["webview.platforms.cocoa", "AppKit", "WebKit"]
else:
    hiddenimports += ["webview.platforms.gtk", "gi"]

a = Analysis(
    ["main.py"],
    pathex=["."],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Alfred",
    debug=False,
    strip=False,
    upx=False,
    console=False,
    icon=_icon_or_none("build/icon.ico") if sys.platform.startswith("win") else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name="Alfred",
)

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="Alfred.app",
        icon=_icon_or_none("build/icon.icns"),
        bundle_identifier="com.alfred.assistant",
        info_plist={
            "NSMicrophoneUsageDescription": "Alfred uses your microphone so you can talk to it.",
            "CFBundleShortVersionString": "0.1.0",
        },
    )
