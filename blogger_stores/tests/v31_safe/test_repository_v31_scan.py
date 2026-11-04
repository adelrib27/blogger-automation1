import copy
from datetime import datetime,timezone
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'blogger_stores'/'src'))
sys.path.insert(0,str(ROOT/'src'))
from v31_shopee_safe_scan import validate_setup, choose, SafeScanError
from shopee_oportunidades_v23 import evaluate_keyword,run_regression_checks

PROFILE=json.loads((ROOT/'blogger_stores/v31_lab/perfil_v31_lab.json').read_text(encoding='utf8'))
CONFIG=json.loads((ROOT/'config/shopee_v31_lab.json').read_text(encoding='utf8'))
RULES=json.loads((ROOT/'config/shopee_v31_lab_intent_rules.json').read_text(encoding='utf8'))
HISTORY=json.loads((ROOT/'blogger_stores/v31_lab/v31_lab_rotation_seed.json').read_text(encoding='utf8'))
NOW=datetime.fromisoformat('2026-11-03T21:45:00-03:00')

class RepoScannerContractTests(unittest.TestCase):
    def test_base_v23_regressions(self):run_regression_checks(RULES)
    def test_config_profile_history_compatible(self):
        self.assertEqual(validate_setup(PROFILE,CONFIG,RULES,HISTORY)[0],PROFILE['blog_id'])
    def test_all_16_intentions_have_hard_rules(self):
        self.assertEqual(sum(map(len,CONFIG['categories'].values())),16)
        for keywords in CONFIG['categories'].values():
            for keyword in keywords:
                self.assertTrue(RULES['rules'][keyword]['require_groups'])
    def test_cross_blog_history_blocked(self):
        other=copy.deepcopy(HISTORY);other['blogId']='1426630233929943394'
        with self.assertRaises(SafeScanError):validate_setup(PROFILE,CONFIG,RULES,other)
    def test_empty_ranking_blocks_before_affiliate_generation(self):
        with self.assertRaises(SafeScanError):choose([],PROFILE,CONFIG,RULES,HISTORY,
            semantic_check=evaluate_keyword,policy_check=lambda _:None,now=NOW)
    def test_unsafe_target_page_blocks(self):
        p={**PROFILE,'page_url':'https://achadosparacasa2026.blogspot.com/p/loja.html'}
        with self.assertRaises(SafeScanError): validate_setup(p,CONFIG,RULES,HISTORY)

if __name__=='__main__':unittest.main()