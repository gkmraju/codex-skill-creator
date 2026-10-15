"""Package installation plus a bounded developer runtime acceptance case."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

SKILL = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("skill_install", SKILL / "scripts/install.py")
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class PackageTests(unittest.TestCase):
    def test_fresh_install_copies_every_resource(self):
        with tempfile.TemporaryDirectory() as folder:
            installed = installer.install(folder)
            expected = {p.relative_to(SKILL).as_posix(): p.read_bytes()
                for p in SKILL.rglob("*") if p.is_file()}
            actual = {p.relative_to(installed).as_posix(): p.read_bytes()
                for p in installed.rglob("*") if p.is_file()}
            self.assertEqual(expected, actual)
            self.assertTrue((installed / "SKILL.md").is_file())

    def test_existing_install_is_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            target = installer.install(folder)
            original = (target / "SKILL.md").read_bytes()
            with self.assertRaises(ValueError):
                installer.install(folder)
            self.assertEqual(original, (target / "SKILL.md").read_bytes())

    def test_missing_project_is_refused(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):
                installer.install(Path(folder) / "missing")

    def test_runtime_behavior(self):
        profile = SKILL.name
        if profile == "polars":
            import polars as pl
            from polars.testing import assert_frame_equal
            with tempfile.TemporaryDirectory() as folder:
                source = Path(folder) / "orders.csv"
                raw = b"id,team,amount\n001,A,10\n002,A,20\n003,B,5\n"
                source.write_bytes(raw)
                lazy = pl.scan_csv(source, schema_overrides={"id": pl.String, "amount": pl.Int64})
                typed = lazy.collect()
                self.assertEqual(typed["id"].to_list(), ["001", "002", "003"])
                query = lazy.group_by("team").agg(pl.col("amount").sum()).sort("team")
                assert_frame_equal(query.collect(), query.collect(engine="streaming"))
                self.assertEqual(query.collect().to_dicts(), [{"team": "A", "amount": 30}, {"team": "B", "amount": 5}])
                duplicate = pl.DataFrame({"id": ["001", "001"], "label": ["a", "b"]})
                with self.assertRaises(pl.exceptions.ComputeError):
                    typed.join(duplicate, on="id", how="left", validate="m:1")
                missing = pl.DataFrame({"x": [None, float("nan"), 2.0]})
                self.assertEqual(missing["x"].null_count(), 1)
                self.assertEqual(missing["x"].is_nan().sum(), 1)
                self.assertEqual(source.read_bytes(), raw)
        elif profile == "networkx":
            import networkx as nx
            graph = nx.Graph()
            graph.add_weighted_edges_from([("api", "cache", 1), ("cache", "db", 2), ("api", "db", 9)])
            self.assertEqual(nx.shortest_path(graph, "api", "db", weight="weight"), ["api", "cache", "db"])
            self.assertEqual(nx.shortest_path_length(graph, "api", "db", weight="weight"), 3)
            self.assertEqual(len(list(nx.connected_components(graph))), 1)
            graph.add_node("isolated")
            self.assertFalse(nx.has_path(graph, "api", "isolated"))
        elif profile == "simpy":
            import simpy
            env = simpy.Environment()
            resource = simpy.Resource(env, capacity=1)
            events = []
            def worker(name):
                with resource.request() as request:
                    yield request
                    events.append((name, "start", env.now))
                    yield env.timeout(2)
                    events.append((name, "done", env.now))
            env.process(worker("first"))
            env.process(worker("second"))
            env.run()
            self.assertEqual(events, [("first", "start", 0), ("first", "done", 2),
                ("second", "start", 2), ("second", "done", 4)])
        else:
            self.fail("Unsupported runtime profile")
