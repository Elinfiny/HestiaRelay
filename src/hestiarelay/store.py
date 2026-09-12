from __future__ import annotations

import os
import sqlite3
from contextlib import closing, contextmanager
from contextvars import ContextVar
from pathlib import Path

from hestiarelay.models import HouseholdState


class SQLiteStateStore:
    def __init__(self, path: str | Path | None = None) -> None:
        configured = path or os.getenv("HESTIA_STATE_DB", "hestiarelay.db")
        self.path = Path(configured)
        self._connection: ContextVar[sqlite3.Connection | None] = ContextVar(
            "state_connection", default=None
        )
        self._initialize()

    @contextmanager
    def transaction(self):
        """Serialize read-modify-write, including nested service/engine calls."""
        if self._connection.get() is not None:
            yield
            return
        with closing(sqlite3.connect(self.path, timeout=30)) as connection:
            connection.execute("BEGIN IMMEDIATE")
            token = self._connection.set(connection)
            try:
                yield
                connection.commit()
            except BaseException:
                connection.rollback()
                raise
            finally:
                self._connection.reset(token)

    @contextmanager
    def connection(self):
        active = self._connection.get()
        if active is not None:
            yield active
        else:
            with closing(sqlite3.connect(self.path, timeout=30)) as connection:
                yield connection
                connection.commit()

    def _initialize(self) -> None:
        with closing(sqlite3.connect(self.path)) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS household_state (
                    singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
                    state_json TEXT NOT NULL
                )
                """
            )
            connection.commit()

    def load(self) -> HouseholdState:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT state_json FROM household_state WHERE singleton = 1"
            ).fetchone()
        if not row:
            return HouseholdState()
        return HouseholdState.model_validate_json(row[0])

    def save(self, state: HouseholdState) -> None:
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO household_state(singleton, state_json)
                VALUES (1, ?)
                ON CONFLICT(singleton) DO UPDATE SET state_json = excluded.state_json
                """,
                (state.model_dump_json(),),
            )

    def reset(self) -> None:
        with self.connection() as connection:
            connection.execute("DELETE FROM household_state WHERE singleton = 1")
