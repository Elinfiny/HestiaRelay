from __future__ import annotations

import os
import sqlite3
from contextlib import closing
from pathlib import Path

from hestiarelay.models import HouseholdState


class SQLiteStateStore:
    def __init__(self, path: str | Path | None = None) -> None:
        configured = path or os.getenv("HESTIA_STATE_DB", "hestiarelay.db")
        self.path = Path(configured)
        self._initialize()

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
        with closing(sqlite3.connect(self.path)) as connection:
            row = connection.execute(
                "SELECT state_json FROM household_state WHERE singleton = 1"
            ).fetchone()
        if not row:
            return HouseholdState()
        return HouseholdState.model_validate_json(row[0])

    def save(self, state: HouseholdState) -> None:
        with closing(sqlite3.connect(self.path)) as connection:
            connection.execute(
                """
                INSERT INTO household_state(singleton, state_json)
                VALUES (1, ?)
                ON CONFLICT(singleton) DO UPDATE SET state_json = excluded.state_json
                """,
                (state.model_dump_json(),),
            )
            connection.commit()

    def reset(self) -> None:
        with closing(sqlite3.connect(self.path)) as connection:
            connection.execute("DELETE FROM household_state WHERE singleton = 1")
            connection.commit()
