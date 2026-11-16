"""C7: seleção de pré-conversão por site sem escanear API e sem publicação."""
import csv
import tempfile
import unittest
from pathlib import Path
from affiliate_hub_v31.catalog import Catalog
from affiliate_hub_v31.link_warmup import warmup_candidates
from affiliate_hub_v31.fallback_v23 import FallbackUnavailable


class WarmupSelectionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        folder=Path(self.tmp.name)
        feed=folder/"feed.csv"
        with feed.open("w",encoding="utf-8",newline="") as io:
            writer=csv.DictWriter(io,fieldnames=["shopId","itemId","productName","productLink","imageUrl"])
            writer.writeheader()
            for id,name in enumerate(["Luminária Solar LED para Jardim",
                                      "Luminária Solar LED de Jardim 2",
                                      "Broca para Furadeira",
                                      "Furadeira de Impacto 12V",
                                      "Luminária de Mesa para Sala"],1):
                writer.writerow({"shopId":"123","itemId":str(id),"productName":name,
                                 "productLink":f"https://shopee.com.br/item-i.123.{id}",
                                 "imageUrl":"https://images.example.invalid/p.png"})
        self.catalog=Catalog(folder/"catalog.sqlite3")
        self.addCleanup(self.catalog.close)
        self.catalog.import_csv(feed,"feed1")

    def test_warmup_uses_only_eligible_keywords_and_missing_campaign_links(self):
        cfg={"categories":{"Area Externa":["luminaria solar jardim"]}}
        rules={"rules":{"luminaria solar jardim":{
            "require_groups":[["luminaria"],["solar"],["jardim"]],"block_phrases":[]}}}
        result=warmup_candidates(self.catalog,"wordpress_casa_decoracao",cfg,rules,3)
        self.assertEqual(result,["shopee:123:1"])
        self.catalog.cache_link("shopee:123:1","casaedecoracaowp",
                                "https://s.shopee.com.br/cached")
        self.assertEqual(warmup_candidates(self.catalog,"wordpress_casa_decoracao",
                                           cfg,rules,1),["shopee:123:2"])
        self.assertEqual(warmup_candidates(self.catalog,"wordpress_radartechbr",
                                           cfg,rules,1),["shopee:123:1"])

    def test_missing_category_is_prioritized_for_next_conversion(self):
        cfg={"categories":{
            "Area Externa":["luminaria solar jardim"],
            "Sala":["luminaria mesa"]
        }}
        rules={"rules":{
            "luminaria solar jardim":{
                "require_groups":[["luminaria"],["solar"],["jardim"]],
                "block_phrases":[]
            }
        }}
        self.catalog.cache_link("shopee:123:1","casaedecoracaowp",
                                "https://s.shopee.com.br/old-area")
        result=warmup_candidates(self.catalog,"wordpress_casa_decoracao",cfg,rules,2)
        self.assertEqual(result[0],"shopee:123:5")
        self.assertEqual(len(result),2)

    def test_unknown_site_and_limits_fail_before_any_api(self):
        with self.assertRaisesRegex(FallbackUnavailable,"site_not_registered"):
            warmup_candidates(self.catalog,"unknown_site",{"categories":{}},{},1)
        for count in (0,4):
            with self.assertRaisesRegex(FallbackUnavailable,"warmup_limit_invalid"):
                warmup_candidates(self.catalog,"wordpress_casa_decoracao",
                                  {"categories":{}},{},count)


if __name__=="__main__":
    unittest.main()
