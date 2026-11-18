"""C45: cron seguro, idempotente, reparo após falha parcial, zero posts."""
import unittest
from unittest.mock import Mock,patch

from affiliate_hub_v31 import universal_maintenance as m


def _reclassification(*,approved=0,products=203649):
    return {
        "mode": "C39_RECLASSIFICATION_APPLY",
        "products": products,
        "supported_candidates_total": approved,
        "approved_this_batch": approved,
        "remaining_review": 194370-approved,
        "old_affiliate_links_preserved": True,
        "shopee_api_calls": 0,
        "publication_calls": 0,
        "r2_writes": int(approved>0),
        "snapshot_verified": bool(approved),
    }


def _index(*,products=203649):
    return {
        "r2_snapshot_saved_and_verified": True,
        "products_indexed": products,
        "new_approvals": 0,
        "publication_calls": 0,
        "converted": 0,
        "r2_writes": 1,
        "index_storage": "R2_SIDECAR",
        "core_catalog_untouched": True,
    }


class UniversalMaintenanceTests(unittest.TestCase):
    def test_manifest_freshness_compares_timezone_aware_instants(self):
        core={"created_utc":"2026-11-18T12:00:00+00:00"}
        equal={"created_utc":"2026-11-18T09:00:00-03:00",
               "product_count":203649}
        old={"created_utc":"2026-11-18T11:59:59Z",
             "product_count":203649}
        self.assertFalse(m.needs_index_rebuild(
            core,equal,expected_products=203649))
        self.assertTrue(m.needs_index_rebuild(
            core,old,expected_products=203649))
        self.assertTrue(m.needs_index_rebuild(
            core,None,expected_products=203649))
        self.assertTrue(m.needs_index_rebuild(
            core,{**equal,"product_count":203648},
            expected_products=203649))
        with self.assertRaises(m.UniversalMaintenanceError):
            m.needs_index_rebuild(
                core,{**equal,"created_utc":"2026-11-18T12:00:00"},
                expected_products=203649)

    def test_rejects_unsafe_limits_without_any_io(self):
        for limit in (0,101,False,True,1.5,"100",-1):
            with self.subTest(limit=limit):
                with self.assertRaises(m.UniversalMaintenanceError):
                    m.maintain_universal(execute=True,limit=limit)
        with self.assertRaises(m.UniversalMaintenanceError):
            m.maintain_universal(execute="true")

    @patch.object(m,"reclassify_r2")
    def test_dry_run_no_credentials_no_storage_write(self,reclassify):
        reclassify.return_value={
            "mode":"DRY_RUN","products":203649,
            "supported_candidates_total":0,
            "approved_this_batch":0,
            "remaining_review":194370,"r2_writes":0}
        result=m.maintain_universal(execute=False)
        self.assertEqual(result["r2_catalog_writes"],0)
        self.assertEqual(result["r2_index_writes"],0)
        self.assertEqual(result["publication_calls"],0)
        self.assertEqual(result["affiliate_conversion_calls"],0)
        reclassify.assert_called_once_with(execute=False,limit=100)

    def _execute_with_mocks(self,*,count=0,core_time="2026-11-18T15:00:00+00:00",
                            index_time="2026-11-18T15:01:00+00:00",
                            index_count=203649,force=False):
        with patch.object(m,"reclassify_r2",return_value=_reclassification(
                approved=count)) as reclassify,\
             patch.object(m,"rebuild_inventory_r2",
                          return_value=_index()) as rebuild,\
             patch.object(m.R2State,"from_env") as state_factory,\
             patch.object(m,"UniversalIndexStorage") as index_cls:
            state_factory.return_value._read_manifest.return_value={
                "created_utc":core_time}
            index_cls.return_value._manifest.return_value={
                "created_utc":index_time,
                "product_count":index_count}
            result=m.maintain_universal(
                execute=True,limit=100,repair_index=force)
            return result,reclassify.call_count,rebuild.call_count

    def test_noop_run_does_not_rewrite_r2(self):
        result,calls,index_calls=self._execute_with_mocks()
        self.assertEqual(calls,1)
        self.assertEqual(index_calls,0)
        self.assertFalse(result["index_reconciled"])
        self.assertEqual(result["r2_catalog_writes"],0)

    def test_reclassifications_rebuild_only_the_sidecar(self):
        result,_,index_calls=self._execute_with_mocks(count=8)
        self.assertEqual(index_calls,1)
        self.assertEqual(result["approved_this_batch"],8)
        self.assertTrue(result["existing_affiliate_links_preserved"])
        self.assertEqual(result["r2_catalog_writes"],1)
        self.assertEqual(result["r2_index_writes"],1)
        self.assertEqual(result["publication_calls"],0)

    def test_repair_after_partial_core_commit(self):
        result,_,index_calls=self._execute_with_mocks(
            core_time="2026-11-18T16:00:00+00:00",
            index_time="2026-11-18T15:00:00+00:00")
        self.assertEqual(result["approved_this_batch"],0)
        self.assertEqual(result["r2_catalog_writes"],0)
        self.assertEqual(index_calls,1)

    def test_missing_products_rebuilds(self):
        result,_,index_calls=self._execute_with_mocks(index_count=203640)
        self.assertTrue(result["index_reconciled"])
        self.assertEqual(index_calls,1)

    def test_explicit_repair_rebuilds(self):
        result,_,index_calls=self._execute_with_mocks(force=True)
        self.assertEqual(index_calls,1)

    @patch.object(m,"reclassify_r2")
    @patch.object(m,"rebuild_inventory_r2")
    @patch.object(m.R2State,"from_env")
    @patch.object(m,"UniversalIndexStorage")
    def test_never_reports_success_for_unverified_core_mutation(
        self,index_cls,state_factory,rebuild,reclassify):
        reclassify.return_value={
            **_reclassification(approved=10),"snapshot_verified":False}
        with self.assertRaisesRegex(m.UniversalMaintenanceError,
                                    "reclassification_integrity_gate_failed"):
            m.maintain_universal(execute=True)
        rebuild.assert_not_called()

    @patch.object(m,"reclassify_r2")
    @patch.object(m,"rebuild_inventory_r2")
    @patch.object(m.R2State,"from_env")
    @patch.object(m,"UniversalIndexStorage")
    def test_detects_incomplete_sidecar_save(
        self,index_cls,state_factory,rebuild,reclassify):
        reclassify.return_value=_reclassification(approved=2)
        state_factory.return_value._read_manifest.return_value={
            "created_utc":"2026-11-18T15:01:00Z"}
        index_cls.return_value._manifest.return_value={
            "created_utc":"2026-11-18T15:00:00Z",
            "product_count":203649}
        rebuild.return_value={**_index(),
                              "r2_snapshot_saved_and_verified":False}
        with self.assertRaisesRegex(m.UniversalMaintenanceError,
                                    "index_reconciliation_failed"):
            m.maintain_universal(execute=True)

    def test_fails_closed_on_invalid_manifest(self):
        with self.assertRaises(m.UniversalMaintenanceError):
            m.needs_index_rebuild(None,None,expected_products=1)


if __name__=="__main__":
    unittest.main()
