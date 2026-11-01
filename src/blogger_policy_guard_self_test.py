#!/usr/bin/env python3
from blogger_policy_guard import (
    cookie_safety_check,
    generated_copy_check,
    product_policy_check,
)


def p(name, offer="https://s.shopee.com.br/abc", image="https://cf.shopee.com.br/file/abc"):
    return {"productName": name, "offerLink": offer, "imageUrl": image}


assert product_policy_check(p("Air Fryer Digital 5L 1500W"))["accepted"]
assert not product_policy_check(p("Cigarro eletrônico Vape Recarregável"))["accepted"]
assert not product_policy_check(p("Oxímetro Digital de Dedo"))["accepted"]
assert not product_policy_check(p("Whey Protein Suplemento Alimentar"))["accepted"]
assert not product_policy_check(p("Pistola Airsoft"))["accepted"]
assert not product_policy_check(p("Produto comum", offer="http://s.shopee.com.br/x"))["accepted"]
assert not product_policy_check(p("Produto comum", offer="https://example.com/x"))["accepted"]
assert not product_policy_check(p("Produto comum", image="https://example.com/img.jpg"))["accepted"]
assert generated_copy_check("Confira opções úteis para sua rotina")["accepted"]
assert not generated_copy_check("Resultado garantido e sem risco")["accepted"]
assert cookie_safety_check("<head><title>Blog</title></head>")["accepted"]
assert not cookie_safety_check("<script>cookieChoices = {};</script>")["accepted"]
assert not cookie_safety_check("<style>.cookie-choices-info{display:none}</style>")["accepted"]
print("blogger_policy_guard_self_test: 13/13 OK")
