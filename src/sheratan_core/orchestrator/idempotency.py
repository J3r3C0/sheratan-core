"""Idempotency storage for relay callbacks."""
from __future__ import annotations

import os
import sqlite3
import threading
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

DEFAULT_IDEMPOTENCY_TTL_SECONDS = int(os.getenv("SHERATAN_IDEMPOTENCY_TTL_SECONDS", "900"))
DEFAULT_MAX_INMEMORY_ENTRIES = int(os.getenv("SHERATAN_IDEMPOTENCY_MAX_ENTRIES", "2048"))
SQLITE_PATH_ENV = "SHERATAN_IDEMPOTENCY_SQLITE_PATH"


class IdempotencyConflictError(RuntimeError):
    """Raised when an idempotency key is reused with a different payload."""

    def __init__(self, key: str) -> None:
        super().__init__(f"Conflicting payload for idempotency key '{key}'")
        self.key = key


@dataclass(frozen=True)
class IdempotencyReservation:
    """Represents the reservation state of an idempotency token."""

    created: bool


class IdempotencyStore(Protocol):
    """Storage backend contract for idempotency reservations."""

    def reserve(self, key: str, fingerprint: str, timestamp: int) -> IdempotencyReservation:
        """Reserve the given key if it has not been seen.

        Returns an :class:`IdempotencyReservation` describing whether the caller
        is the creator of the reservation. Implementations must raise
        :class:`IdempotencyConflictError` if the key already exists but with a
        different fingerprint.
        """

    def clear(self) -> None:
        """Remove all stored reservations (used for testing)."""


class InMemoryIdempotencyStore:
    """LRU idempotency cache backed by an :class:`OrderedDict`."""

    def __init__(self, ttl_seconds: int = DEFAULT_IDEMPOTENCY_TTL_SECONDS, max_entries: int = DEFAULT_MAX_INMEMORY_ENTRIES) -> None:
        self._ttl_seconds = ttl_seconds
        self._max_entries = max_entries
        self._entries: "OrderedDict[str, tuple[str, int]]" = OrderedDict()
        self._lock = threading.Lock()

    def _evict_expired(self, cutoff: int) -> None:
        keys_to_delete = [k for k, (_, ts) in self._entries.items() if ts < cutoff]
        for key in keys_to_delete:
            self._entries.pop(key, None)

    def reserve(self, key: str, fingerprint: str, timestamp: int) -> IdempotencyReservation:
        cutoff = timestamp - self._ttl_seconds
        with self._lock:
            if cutoff > 0:
                self._evict_expired(cutoff)

            record = self._entries.get(key)
            if record:
                stored_fingerprint, _ = record
                if stored_fingerprint != fingerprint:
                    raise IdempotencyConflictError(key)
                self._entries.move_to_end(key)
                return IdempotencyReservation(created=False)

            self._entries[key] = (fingerprint, timestamp)
            self._entries.move_to_end(key)
            while len(self._entries) > self._max_entries:
                self._entries.popitem(last=False)
            return IdempotencyReservation(created=True)

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()


class SQLiteIdempotencyStore:
    """Persistent idempotency cache backed by SQLite."""

    def __init__(self, path: Path, ttl_seconds: int = DEFAULT_IDEMPOTENCY_TTL_SECONDS) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self._path = path
        self._ttl_seconds = ttl_seconds
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS idempotency_records (
                key TEXT PRIMARY KEY,
                fingerprint TEXT NOT NULL,
                timestamp INTEGER NOT NULL
            )
            """
        )
        self._conn.commit()

    def _purge_expired(self, cutoff: int) -> None:
        if cutoff <= 0:
            return
        self._conn.execute("DELETE FROM idempotency_records WHERE timestamp < ?", (cutoff,))
        self._conn.commit()

    def reserve(self, key: str, fingerprint: str, timestamp: int) -> IdempotencyReservation:
        cutoff = timestamp - self._ttl_seconds
        with self._lock:
            self._purge_expired(cutoff)
            row = self._conn.execute(
                "SELECT fingerprint FROM idempotency_records WHERE key = ?", (key,)
            ).fetchone()
            if row:
                (stored_fingerprint,) = row
                if stored_fingerprint != fingerprint:
                    raise IdempotencyConflictError(key)
                return IdempotencyReservation(created=False)

            self._conn.execute(
                "INSERT OR REPLACE INTO idempotency_records(key, fingerprint, timestamp) VALUES (?, ?, ?)",
                (key, fingerprint, timestamp),
            )
            self._conn.commit()
            return IdempotencyReservation(created=True)

    def clear(self) -> None:
        with self._lock:
            self._conn.execute("DELETE FROM idempotency_records")
            self._conn.commit()


def create_idempotency_store() -> IdempotencyStore:
    """Create an idempotency store based on the configured backend."""

    sqlite_path = os.getenv(SQLITE_PATH_ENV, "").strip()
    ttl_seconds = int(os.getenv("SHERATAN_IDEMPOTENCY_TTL_SECONDS", str(DEFAULT_IDEMPOTENCY_TTL_SECONDS)))
    if sqlite_path:
        return SQLiteIdempotencyStore(Path(sqlite_path), ttl_seconds=ttl_seconds)
    max_entries = int(os.getenv("SHERATAN_IDEMPOTENCY_MAX_ENTRIES", str(DEFAULT_MAX_INMEMORY_ENTRIES)))
    return InMemoryIdempotencyStore(ttl_seconds=ttl_seconds, max_entries=max_entries)
