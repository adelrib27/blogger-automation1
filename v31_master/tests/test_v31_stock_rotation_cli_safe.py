#!/usr/bin/env python3
"""CLI do plano de rotacao; testa separacao entre blogs e inexistencia de PUT."""
from __future__ import annotations
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import store_stock_commission_safe as policy
from test_v31_store_stock_commission_safe import existing, offers, inventory


class TestStockCliSafe(unittest.TestCase):
    BLOG_ID = "8476663092477971560"

    def make_inputs(self, temp, *, confirmed=True, bad_blog=False, mode="LAB_SAFE_ONLY", no_candidate=False, api_status="OK", graphql_codes=None, api_http=200, include_meta=True):
        base = Path(temp)
        target = self.BLOG_ID
        cur, cand, inv = [base / name for name in ("current.json", "offers.json", "inventory.json")]
        old = existing()
        now = datetime.now(timezone.utc)
        observations = [
            inventory(old[0]["item_id"], now - timedelta(minutes=40), 0, run="stock-check-early"),
            inventory(old[0]["item_id"], now - timedelta(minutes=4), 0, run="stock-check-late"),
        ] if confirmed else []
        cur.write_text(json.dumps({"blog_id": target, "count": 16, "products": old}), encoding="utf-8")
        record = {"blog_id": target if not bad_blog else "000000",
                  "categories": offers(alt=not no_candidate)}
        if include_meta:
            record["discovery"] = {
                "operation": "productOfferV2",
                "http_status": api_http,
                "query_status": api_status,
                "graphql_error_codes": [] if graphql_codes is None else graphql_codes,
            }
        cand.write_text(json.dumps(record), encoding="utf-8")
        inv.write_text(json.dumps({"blog_id": target, "observations": observations}), encoding="utf-8")
        out = base / "output"
        argv = ["--profile", str(base / "profile.json"),
                "--current", str(cur), "--offers", str(cand),
                "--inventory", str(inv), "--out-dir", str(out)]
        return argv, out, {"mode": mode, "target": {"blog_id": target}}

    def run_case(self, temp, **kwargs):
        argv, out, config = self.make_inputs(temp, **kwargs)
        with patch("replication_safe.load_profile", return_value=config):
            stream = io.StringIO()
            with redirect_stdout(stream):
                code = policy.run_lab_cli(argv)
        result = json.loads(stream.getvalue())
        return code, out, result

    def test_confirmed_out_of_stock_creates_safe_candidate_not_put(self):
        with tempfile.TemporaryDirectory() as temp:
            code, out, result = self.run_case(temp)
            self.assertEqual(code, 0)
            self.assertFalse(result["writes_blogger"])
            self.assertEqual(result["stock_replacements"], 1)
            self.assertTrue((out / "loja_candidata_safe.html").exists())
            html = (out / "loja_candidata_safe.html").read_text(encoding="utf-8")
            self.assertEqual(html.count('class="ub-product-card"'), 16)
            self.assertIn('data-lab-only="true"', html)
            data = json.loads((out / "loja_plano_safe.json").read_text(encoding="utf-8"))
            self.assertEqual(data["summary"]["target_blog_id"], self.BLOG_ID)

    def test_unknown_stock_never_creates_candidate(self):
        with tempfile.TemporaryDirectory() as temp:
            code, out, result = self.run_case(temp, confirmed=False)
            self.assertEqual(code, 0)
            self.assertEqual(result["status"], "NO_CONFIRMED_STOCK_CHANGE")
            self.assertFalse(out.exists())

    def test_wrong_blog_inputs_fail_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            code, out, result = self.run_case(temp, bad_blog=True)
            self.assertEqual(code, 2)
            self.assertFalse(out.exists())
            self.assertFalse(result["writes_blogger"])

    def test_live_profile_does_not_run(self):
        with tempfile.TemporaryDirectory() as temp:
            code, out, result = self.run_case(temp, mode="PRODUCTION")
            self.assertEqual(code, 2)
            self.assertFalse(out.exists())

    def test_no_replacement_no_file_created(self):
        with tempfile.TemporaryDirectory() as temp:
            code, out, result = self.run_case(temp, no_candidate=True)
            self.assertEqual(code, 0)
            self.assertEqual(result["status"], "BLOCK_NO_VERIFIED_REPLACEMENT")
            self.assertFalse(out.exists())

    def test_existing_out_directory_blocks_second_write(self):
        with tempfile.TemporaryDirectory() as temp:
            argv, out, config = self.make_inputs(temp)
            out.mkdir()
            (out / "parallel_worker.txt").write_text("preserve me", encoding="utf-8")
            with patch("replication_safe.load_profile", return_value=config):
                with redirect_stdout(io.StringIO()):
                    code = policy.run_lab_cli(argv)
            self.assertEqual(code, 2)
            self.assertEqual((out / "parallel_worker.txt").read_text(encoding="utf-8"), "preserve me")


    def test_graphql_10000_blocks_rotation_even_with_stock_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            code, out, result = self.run_case(
                temp, api_status="ERROR", graphql_codes=[10000])
            self.assertEqual(code, 2)
            self.assertFalse(result["writes_blogger"])
            self.assertFalse(out.exists())

    def test_http_200_with_graphql_error_blocks(self):
        with tempfile.TemporaryDirectory() as temp:
            code, out, result = self.run_case(
                temp, api_status="OK", graphql_codes=[10000])
            self.assertEqual(code, 2)
            self.assertFalse(out.exists())

    def test_http_failure_blocks_rotation(self):
        with tempfile.TemporaryDirectory() as temp:
            code, out, result = self.run_case(temp, api_http=503)
            self.assertEqual(code, 2)
            self.assertFalse(out.exists())

    def test_missing_discovery_proof_blocks(self):
        with tempfile.TemporaryDirectory() as temp:
            code, out, result = self.run_case(temp, include_meta=False)
            self.assertEqual(code, 2)
            self.assertFalse(out.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
