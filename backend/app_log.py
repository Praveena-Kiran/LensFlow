"""
Logging for the packaged app, which has no console window.

install() copies everything printed (stdout and stderr) into lensflow.log in
the user's data folder, alongside the console when there is one, and records
uncaught exceptions with their traceback. The log is trimmed when it grows
past MAX_BYTES so it never fills the disk.
"""

import datetime
import os
import sys
import threading
import traceback

from backend.paths import user_data_dir


LOG_NAME = "lensflow.log"
MAX_BYTES = 1_000_000     # trim to the newest half beyond this

_installed = False
_on_crash = None


def log_path():
    return os.path.join(user_data_dir(), LOG_NAME)


class _Tee:
    """Writes to the log file and (if any) the original stream."""

    def __init__(self, original, handle, lock):
        self.original = original
        self.handle = handle
        self.lock = lock

    def write(self, text):
        if self.original is not None:
            try:
                self.original.write(text)
            except Exception:
                pass
        with self.lock:
            try:
                self.handle.write(text)
                self.handle.flush()
            except Exception:
                pass
        return len(text)

    def flush(self):
        if self.original is not None:
            try:
                self.original.flush()
            except Exception:
                pass

    def isatty(self):
        return False


def _trim(path):
    try:
        if os.path.getsize(path) > MAX_BYTES:
            with open(path, "rb") as f:
                f.seek(-MAX_BYTES // 2, os.SEEK_END)
                tail = f.read()
            with open(path, "wb") as f:
                f.write(b"[... older log lines removed ...]\n" + tail)
    except OSError:
        pass


def _excepthook(kind, value, tb):
    text = "".join(traceback.format_exception(kind, value, tb))
    print(f"\n💥 Uncaught error:\n{text}", file=sys.stderr)
    if _on_crash is not None:
        try:
            _on_crash(value)
        except Exception:
            pass


def install(on_crash=None):
    """Start logging. `on_crash(exception)` is called for uncaught errors."""

    global _installed, _on_crash
    _on_crash = on_crash

    if _installed:
        return log_path()

    path = log_path()
    _trim(path)

    handle = open(path, "a", encoding="utf-8", errors="replace")
    lock = threading.Lock()

    from backend.app_info import APP_NAME, VERSION
    handle.write(
        f"\n===== {APP_NAME} {VERSION} started "
        f"{datetime.datetime.now():%Y-%m-%d %H:%M:%S} =====\n"
    )
    handle.flush()

    sys.stdout = _Tee(sys.stdout, handle, lock)
    sys.stderr = _Tee(sys.stderr, handle, lock)

    sys.excepthook = _excepthook
    threading.excepthook = lambda args: _excepthook(args.exc_type, args.exc_value, args.exc_traceback)

    _installed = True
    return path
