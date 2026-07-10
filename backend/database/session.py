from __future__ import annotations

from contextlib import contextmanager

class DummyEngine:
    def dispose(self):
        pass

engine = DummyEngine()
SessionLocal = lambda: None

@contextmanager
def session_scope():
    """Mock session scope that bypasses SQLAlchemy and yields None."""
    try:
        yield None
    except Exception:
        raise
