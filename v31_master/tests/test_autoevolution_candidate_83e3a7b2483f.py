import unittest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from store_stock_commission_safe import commission_eligible

class TestStrictAffiliateVerification(unittest.TestCase):
    def test_only_boolean_true_confirms_origin(self):
        for unverified in ('false', 'true', 1, [True], {'verified': True}, False, None):
            with self.subTest(value=unverified):
                self.assertFalse(commission_eligible({'commissionRate': '0.015'},
                                                    verified_affiliate_response=unverified))

    def test_confirmed_positive_commission_stays_eligible(self):
        self.assertTrue(commission_eligible({'commissionRate': '0.0001'},
                                           verified_affiliate_response=True))

    def test_zero_commission_stays_ineligible(self):
        self.assertFalse(commission_eligible({'commissionRate': '0'},
                                            verified_affiliate_response=True))
