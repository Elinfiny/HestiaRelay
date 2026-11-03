"""The applicability proof must fail when source gains an unreviewed SQL surface."""

import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location("sqlite_surface", Path("scripts/sqlite_surface.py"))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_current_inventory():
    result = module.inspect_sqlite_surface(Path("src/hestiarelay"))
    assert result["sqlite_fixed_sql_only"]
    assert len(result["queries"]) == 10


@pytest.mark.parametrize(
    "statement",
    ["db.execute(user_sql)", 'db.execute("CREATE VIRTUAL TABLE unreviewed")',
     'db.executescript("SELECT 1")', 'db.enable_load_extension(True)'],
)
def test_unreviewed_sql_is_rejected(tmp_path, statement):
    (tmp_path / "store.py").write_text(statement)
    with pytest.raises(AssertionError):
        module.inspect_sqlite_surface(tmp_path)
