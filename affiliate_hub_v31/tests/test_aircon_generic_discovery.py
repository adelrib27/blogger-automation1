"""Testes off-line C93: busca ampla SEM API, sem mutation, sem publicação."""
import unittest
from unittest.mock import patch

from affiliate_hub_v31.aircon_discovery import (
    PRIMARY_KEYWORD, discover, is_whole_air_conditioner,
    listing_key, make_identity, valid_listing,
)


def sample(shop="100", item="200", title="Ar Condicionado Janela Consul 7500 BTUs Frio CCB07GB 127V"):
    return {
        "shopId": shop, "itemId": item, "productName": title,
        "productLink": f"https://shopee.com.br/product/{shop}/{item}",
        "offerLink": "https://s.shopee.com.br/test0000",
        "imageUrl": "https://cf.shopee.com.br/file/test",
        "priceMin": "1999", "periodEndTime": None,
    }


class AirconC93Tests(unittest.TestCase):
    def test_first_keyword_is_generic(self):
        self.assertEqual(PRIMARY_KEYWORD, "ar condicionado")

    def test_real_appliances_multiple_capacities(self):
        for title in (
            "Ar Condicionado Split Gree Inverter 18000 BTUs Frio 220V",
            "Ar condicionado janela Consul 7.500 BTUs Frio",
            "Ar Condicionado Split Samsung 24000BTU Quente e Frio",
            "Ar Condicionado Portatil Philco 10000 BTUs Frio",
        ):
            with self.subTest(title=title):
                self.assertTrue(is_whole_air_conditioner(title))

    def test_accessories_and_fake_units_are_rejected(self):
        for title in (
            "Ar Condicionado Oribreeze Resfriador de Ar Portatil com Luz Noturna",
            "102 Pcs R134A Valvula de Nucleo Ar Condicionado Automotivo",
            "Moldura Para Ar Condicionado de Janela 30000BTUs",
            "Caixa Caixonete Madeira para Ar Condicionado de Janela 7500BTUs",
            "Caixilho Madeira Ar Condicionado de Janela 12000BTUs",
            "Tira Veda Espuma Para Ar Condicionado Janela Split 21000BTU",
            "Comando de Ar Condicionado do Painel VW Up",
            "Evaporadora Ar Condicionado Ford Fusion",
            "Controle Remoto Universal Para Ar Condicionado Split",
            "Mini Ar Condicionado Climatizador USB",
            "Ar condicionado ar quente condensadora avulsa",
            "Turbina Evaporadora 12000BTUs Ar Condicionado Inverter Midea",
            "Ar Condicionado 12V 7000BTUs para Caminhao Motorhomes",
        ):
            with self.subTest(title=title):
                self.assertFalse(is_whole_air_conditioner(title))

    def test_valid_listing_must_match_shop_item_photo_link_and_positive_price(self):
        node=sample()
        self.assertTrue(valid_listing(node))
        self.assertEqual(listing_key(node), "100:200")
        self.assertFalse(valid_listing({**node,"productLink":
            "https://shopee.com.br/product/100/201"}))
        self.assertFalse(valid_listing({**node,"priceMin":"0"}))
        self.assertFalse(valid_listing({**node,"imageUrl":"http://example.com/x.jpg"}))
        self.assertFalse(valid_listing({**node,"offerLink":"https://random.example/abc"}))

    def test_identity_groups_identical_technical_variant_only(self):
        one=sample(shop="101",item="201")
        two=sample(shop="102",item="202")
        other=sample(shop="103",item="203",title=one["productName"].replace("127V","220V"))
        self.assertEqual(make_identity(one),make_identity(two))
        self.assertNotEqual(make_identity(one),make_identity(other))
        without_model=sample(shop="104",item="204",title="Ar Condicionado Janela Consul 7500 BTUs Frio")
        self.assertEqual(make_identity(without_model),"listing:104:204")

    def test_generic_results_accessories_then_safe_fallback(self):
        bad=sample(shop="6",item="7",title="Moldura Para Ar Condicionado de Janela 12000BTU")
        good=sample(shop="9",item="10")
        calls=[]
        def fake_request(app,secret,keyword,page):
            calls.append((keyword,page))
            if keyword=="ar condicionado":
                return {"nodes":[bad],"pageInfo":{"hasNextPage":True}}
            if keyword=="ar condicionado split":
                return {"nodes":[good],"pageInfo":{"hasNextPage":False}}
            return {"nodes":[],"pageInfo":{"hasNextPage":False}}
        with patch("affiliate_hub_v31.aircon_discovery.request_page",fake_request):
            with patch("affiliate_hub_v31.aircon_discovery.load_history",return_value=(set(),set())):
                output=discover("dummy","dummy",rotation_override=0)
        self.assertEqual(output["status"],"READ_ONLY_CANDIDATES")
        self.assertEqual(output["queries"],4)
        self.assertEqual(output["new_listing_candidates"],1)
        self.assertEqual(output["candidates"][0]["listing_key"],"9:10")
        self.assertFalse(output["candidates"][0]["stock_confirmed"])
        self.assertEqual(calls[:2],[("ar condicionado",1),("ar condicionado split",1)])


if __name__=="__main__":
    unittest.main()
