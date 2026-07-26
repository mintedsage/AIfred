# Building installers

This turns Alfred into double-click installers for Windows, macOS, and Linux,
using GitHub Actions' free hosted runners (real Windows/macOS/Linux machines
in the cloud) — so you don't need to own all three platforms yourself.

## One-time setup

1. Push this project to a GitHub repo (create one at github.com/new, then
   `git init && git add -A && git commit -m "Alfred" && git remote add origin <url> && git push -u origin main`).
2. That's it — `.github/workflows/build.yml` is already wired up.

## Building a release

```
git tag v0.1.0
git push --tags
```

This triggers three parallel jobs (Windows/macOS/Linux), each of which:
1. Installs Python + your `requirements.txt` + PyInstaller
2. Runs `pyinstaller alfred.spec` to bundle Alfred + a Python runtime
3. Wraps that into a real installer:
   - **Windows** → `Alfred-Setup-0.1.0-win.exe` (via Inno Setup)
   - **macOS** → `Alfred-0.1.0-mac.dmg` (via `hdiutil`)
   - **Linux** → `Alfred-0.1.0-linux-x86_64.AppImage`
4. Attaches all three to a GitHub Release automatically.

You (or anyone) can then download them straight from your repo's Releases page.

## Testing a build without tagging

Go to the **Actions** tab on GitHub → "Build Alfred installers" → **Run workflow**.
This runs the same pipeline without needing a version tag, so you can check a
build works before calling it a real release.

## Known limitations (be upfront about these when you sell it)

- **Not code-signed.** Windows SmartScreen and macOS Gatekeeper will both
  show an "unknown publisher" warning on first launch. Users can still run
  it (Windows: "More info" → "Run anyway"; Mac: right-click → "Open"), but
  it looks scarier than a signed app. Proper signing costs money — a Windows
  code-signing cert (~$100-300/yr) or an Apple Developer account ($99/yr) —
  worth it once you have real paying customers, not before.
- **Ollama is a separate install.** Alfred doesn't bundle Ollama itself
  (it's a system service, not a Python library) — the Windows installer
  checks for it and prompts if missing; do the same messaging on your
  product page/download instructions for Mac/Linux.
- **First run downloads the AI models** (embedding model + Whisper, a few
  hundred MB total) — mention this on your download page so users aren't
  surprised, especially on slower connections.
- **Icons are placeholders.** Add real `build/icon.ico` (Windows),
  `build/icon.icns` (macOS), and `build/icon.png` (Linux) before a public
  launch — the build works without them, just with a generic icon.
