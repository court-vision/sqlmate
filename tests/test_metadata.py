import importlib.util
import sys
import types
import unittest
from contextlib import contextmanager
from pathlib import Path


class _FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return self._rows


class _FakeSession:
    def __init__(self):
        self.calls = []

    def execute(self, query, params=None):
        sql = str(query)
        params = params or {}
        self.calls.append((sql, params))

        if "information_schema.columns" in sql:
            return _FakeResult([
                ("nba", "players", "id", "integer"),
                ("nba", "player_game_stats", "player_id", "integer"),
            ])

        if "information_schema.tables" in sql:
            return _FakeResult([
                ("nba", "players"),
                ("nba", "player_game_stats"),
            ])

        if "pg_catalog.pg_constraint" in sql:
            if params["table_name"] == "player_game_stats":
                return _FakeResult([("player_id", "nba", "players", "id")])
            return _FakeResult([])

        raise AssertionError(f"Unexpected SQL: {sql}")


def _load_metadata_module():
    fake_session = _FakeSession()

    constants = types.ModuleType("sqlmate.backend.utils.constants")
    constants.DB_NAME = "railway"
    constants.DB_TYPE = "postgresql"
    constants.DB_SCHEMA = "nba"

    db = types.ModuleType("sqlmate.backend.utils.db")

    @contextmanager
    def session_scope(_which="user"):
        yield fake_session

    db.session_scope = session_scope

    module_path = (
        Path(__file__).parents[1]
        / "src/sqlmate/backend/classes/metadata.py"
    )
    spec = importlib.util.spec_from_file_location("metadata_under_test", module_path)
    module = importlib.util.module_from_spec(spec)

    replacements = {
        "sqlmate.backend.utils.constants": constants,
        "sqlmate.backend.utils.db": db,
    }
    original_modules = {name: sys.modules.get(name) for name in replacements}
    try:
        sys.modules.update(replacements)
        spec.loader.exec_module(module)
    finally:
        for name, original in original_modules.items():
            if original is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = original

    return module, fake_session


class PostgresMetadataTests(unittest.TestCase):
    def test_builds_bidirectional_join_edges_from_pg_catalog(self):
        module, _ = _load_metadata_module()

        stats_edges = [str(edge) for edge in module.metadata.get_edges("nba.player_game_stats")]
        player_edges = [str(edge) for edge in module.metadata.get_edges("nba.players")]

        self.assertEqual(
            stats_edges,
            ["nba.player_game_stats.player_id=nba.players.id"],
        )
        self.assertEqual(
            player_edges,
            ["nba.players.id=nba.player_game_stats.player_id"],
        )

    def test_automatic_join_finds_the_foreign_key_path(self):
        module, _ = _load_metadata_module()

        path = module.metadata.shortest_path_from_set(
            {"nba.players"},
            "nba.player_game_stats",
        )

        self.assertEqual(len(path), 1)
        table, edge = path[0]
        self.assertEqual(table, "nba.player_game_stats")
        self.assertEqual(
            str(edge),
            "nba.players.id=nba.player_game_stats.player_id",
        )

    def test_foreign_key_discovery_uses_pg_catalog(self):
        _, fake_session = _load_metadata_module()

        fk_queries = [
            sql for sql, _ in fake_session.calls
            if "pg_catalog.pg_constraint" in sql
        ]

        self.assertEqual(len(fk_queries), 2)
        self.assertTrue(all(
            "information_schema.table_constraints" not in sql
            for sql in fk_queries
        ))
        self.assertTrue(all("WITH ORDINALITY" in sql for sql in fk_queries))


if __name__ == "__main__":
    unittest.main()
