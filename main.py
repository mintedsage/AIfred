"""
main.py — launch Alfred as a desktop app.

Starts the local FastAPI server (bound to 127.0.0.1 only) in a background
thread, then opens a native desktop window pointing at it via pywebview.
If pywebview isn't available (e.g. missing system dependency), falls back
to printing the local URL so it can be opened in a browser instead.
"""

import threading
import time
import webbrowser

import uvicorn

from config import UI_HOST, UI_PORT


def run_server():
    from ui.app import app
    uvicorn.run(app, host=UI_HOST, port=UI_PORT, log_level="warning")


def main():
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    time.sleep(1.0)  # give uvicorn a moment to bind before we point a window at it

    url = f"http://{UI_HOST}:{UI_PORT}"

    try:
        import webview
        webview.create_window("Alfred", url, width=1100, height=760, min_size=(760, 520))
        webview.start()
    except Exception as e:
        print(f"[Alfred] Desktop window unavailable ({e}); opening in your default browser instead.")
        webbrowser.open(url)
        print(f"[Alfred] Running at {url} — press Ctrl+C to stop.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
