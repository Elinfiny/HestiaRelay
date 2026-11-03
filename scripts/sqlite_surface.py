"""Fail closed when the reviewed fixed-SQL application surface changes.

This does not certify arbitrary database files or waive a vendor vulnerability.
The release scope allows only application-created fictional-household databases.
"""

import ast
import re
from pathlib import Path


def inspect_sqlite_surface(root: Path):
    queries = []
    for path in sorted(root.rglob("*.py")):
        for node in ast.walk(ast.parse(path.read_text())):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                continue
            method = node.func.attr
            if method in {
                "executescript", "executemany", "load_extension", "enable_load_extension"
            }:
                raise AssertionError("Unreviewed SQL or extension interface")
            if method != "execute":
                continue
            assert path.name in {"store.py", "recovery.py"}, "SQL outside reviewed modules"
            assert node.args and isinstance(node.args[0], ast.Constant), "Dynamic SQL"
            sql = node.args[0].value
            assert isinstance(sql, str), "SQL must be a fixed string"
            assert not re.search(
                r"\b(WITH|MATCH|COLLATE|ATTACH|DETACH|VIRTUAL|LOAD_EXTENSION)\b", sql, re.I
            ), "Unreviewed SQL feature"
            queries.append({"file": path.name, "line": node.lineno, "sql": " ".join(sql.split())})
    assert len(queries) == 10, "Reviewed SQL inventory changed"
    return {"sqlite_fixed_sql_only": True, "sqlite_no_fts_or_changesets": True, "queries": queries}
