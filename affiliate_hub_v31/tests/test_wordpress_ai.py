"""C59 — contrato de saída estruturada Workers AI nos WordPress."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from affiliate_hub_v31.wordpress_ai import (
    DEFAULT_MODEL,WordPressAIError,build_payload,extract_response,
    request_workers_text,
)

ACCOUNT="a"*32
TOKEN="test-token-not-real-123456789"


class FakeResponse:
    def __init__(self,body):
        self.body=body
    def __enter__(self):return self
    def __exit__(self,*args):return False
    def read(self):return json.dumps(self.body).encode()


class WordPressWorkersAITests(unittest.TestCase):
    def test_supported_model_and_json_format_are_explicit(self):
        self.assertEqual(
            DEFAULT_MODEL,"@cf/meta/llama-3.3-70b-instruct-fp8-fast")
        plan=build_payload("Plano editorial sobre cadeira para varanda",
                           kind="plan")
        self.assertEqual(plan["response_format"]["type"],"json_schema")
        self.assertEqual(
            set(plan["response_format"]["json_schema"]["required"]),
            {"title","keyword","reader_need","product_connection"})
        cta=build_payload("Gere texto contextual para consultar produto",
                          kind="cta")
        self.assertEqual(
            cta["response_format"]["json_schema"]["required"],["lead"])
        html=build_payload("Escreva HTML editorial válido para este post",
                           kind="html")
        self.assertNotIn("response_format",html)

    def test_accepts_parsed_json_object_from_cloudflare(self):
        response={"result":{"response":{"title":"Guia Casa",
           "keyword":"cadeira","reader_need":"orientação",
           "product_connection":"cadeira anunciada"}}}
        plan=json.loads(extract_response(response))
        self.assertEqual(plan["keyword"],"cadeira")
        cta=json.loads(extract_response(
            {"result":{"response":{"lead":"Texto comercial neutro"}}}))
        self.assertIn("lead",cta)

    def test_html_body_is_plain_text_not_forced_into_json(self):
        html="<h2>Como escolher</h2><p>Confira as medidas.</p>"
        self.assertEqual(extract_response(
            {"result":{"response":html}}),html)

    def test_one_real_http_contract_without_network(self):
        response={"result":{"response":{"lead":"Para quem pesquisa sofá, "
                  "confira a especificação no anúncio."}}}
        with patch("affiliate_hub_v31.wordpress_ai.urllib.request.urlopen",
                   return_value=FakeResponse(response)) as mock:
            text=request_workers_text(prompt="Crie um CTA neutro e revisável",
                account_id=ACCOUNT,api_token=TOKEN,kind="cta",retries=1)
            self.assertIn("lead",json.loads(text))
            req=mock.call_args.args[0]
            self.assertIn("api.cloudflare.com",req.full_url)
            body=json.loads(req.data.decode())
            self.assertEqual(body["response_format"]["type"],"json_schema")
            self.assertEqual(body["messages"][0]["role"],"system")
            self.assertNotIn("qwen",req.full_url.lower())

    def test_secrets_and_invalid_response_fail_closed(self):
        with self.assertRaisesRegex(WordPressAIError,
                                    "workers_ai_credentials_unavailable"):
            request_workers_text(prompt="Teste algum artigo original",
                account_id="invalid",api_token=TOKEN,retries=1)
        with self.assertRaisesRegex(WordPressAIError,
                                    "workers_ai_response_unsuccessful"):
            extract_response({"success":False,"result":{"response":"ok"}})
        with self.assertRaisesRegex(WordPressAIError,
                                    "workers_ai_response_empty"):
            extract_response({"result":{}})

    def test_all_three_wp_generators_use_common_client(self):
        root=Path(__file__).resolve().parents[2]
        for folder in ("casa_decoracao","oficina_garagem","radar_tech_br"):
            code=(root/folder/"src"/"generate_articles.py").read_text(
                encoding="utf-8")
            with self.subTest(folder=folder):
                self.assertIn("request_workers_text(",code)
                self.assertIn("kind=\"plan\"",code)
                self.assertIn("kind=\"cta\"",code)
                self.assertIn("DEFAULT_MODEL",code)
                self.assertNotIn("qwen/qwen3-30b-a3b-fp8",code)


if __name__=="__main__":
    unittest.main()
