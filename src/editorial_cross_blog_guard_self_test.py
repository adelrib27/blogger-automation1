#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from editorial_cross_blog_guard import is_collision, run_guard, similarity

CONFIG = {
    "version": 1,
    "projects": {
        "casa_decoracao": {"path": "casa_decoracao", "generated_dir": "data/generated"},
        "oficina_garagem": {"path": "oficina_garagem", "generated_dir": "data/generated"},
        "radar_tech_br": {"path": "radar_tech_br", "generated_dir": "data/generated"},
    },
    "min_editorial_words": 120,
    "shingle_size": 5,
    "thresholds": {
        "sequence": 0.72,
        "sequence_very_high": 0.88,
        "cosine": 0.80,
        "shingle_jaccard": 0.24,
        "shingle_jaccard_high": 0.58,
        "shingle_containment": 0.58,
        "title_jaccard": 0.86,
        "title_body_cosine": 0.68,
        "title_body_containment": 0.32,
    },
}

BASE = """
<h2>Como organizar uma bancada de ferramentas</h2>
<p>Manter ferramentas separadas por função facilita a rotina e reduz o tempo procurando peças.
Antes de começar, retire objetos sem uso, limpe a superfície e agrupe chaves, alicates e acessórios.</p>
<p>Use caixas identificadas para itens pequenos e deixe as ferramentas mais usadas em local de acesso rápido.
Revise a organização periodicamente para que o sistema continue funcional e simples de manter.</p>
""" * 8

NEAR = BASE.replace("ferramentas", "equipamentos").replace("rotina", "atividade")

DISTINCT = """
<h2>Como planejar a iluminação de uma sala pequena</h2>
<p>A luz de um ambiente depende da entrada natural, das cores das paredes e das atividades realizadas no espaço.
Uma luminária de apoio pode complementar a iluminação geral sem exigir mudanças estruturais.</p>
<p>Observe temperatura de cor, posição dos pontos elétricos e intensidade necessária para leitura ou descanso.
As dimensões do cômodo e a distribuição luminosa ajudam a escolher uma solução equilibrada.</p>
""" * 8

BOILERPLATE = """
<div class="affiliate">Transparência: este é um link de afiliado. Preço e disponibilidade podem variar.
<a rel="nofollow sponsored noopener">Confira os detalhes no anúncio.</a></div>
"""


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def pure_similarity_tests() -> None:
    thresholds = CONFIG["thresholds"]

    same = similarity("Organize sua bancada", BASE, "Outro título", BASE)
    assert is_collision(same, thresholds, True)[0], "corpo idêntico deveria bloquear"

    near = similarity("Organize sua bancada", BASE, "Guia da bancada", NEAR)
    assert is_collision(near, thresholds, True)[0], "near-duplicate deveria bloquear"

    different = similarity(
        "Organize sua bancada",
        BASE,
        "Iluminação para sala",
        DISTINCT,
    )
    assert not is_collision(different, thresholds, True)[0], (
        "artigos distintos não deveriam bloquear"
    )

    title_only = similarity(
        "Mesmo título editorial",
        BASE,
        "Mesmo título editorial",
        "",
    )
    assert is_collision(title_only, thresholds, False)[0], (
        "título publicado idêntico deveria bloquear"
    )


def integration_test() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        write_json(root / "config/editorial_cross_blog_guard.json", CONFIG)

        write_json(
            root / "oficina_garagem/data/publication_history.json",
            {
                "items": [
                    {
                        "shopee_item_id": "REF-1",
                        "editorial_title": "Guia da bancada",
                        "wordpress_url": "https://example.invalid/ref-1/",
                    }
                ]
            },
        )
        write_json(root / "oficina_garagem/data/editorial_queue.json", {"items": []})
        write_json(
            root / "oficina_garagem/data/generated/001.json",
            {
                "id": 1,
                "shopee_item_id": "REF-1",
                "status": "GENERATED",
                "editorial_title": "Guia da bancada",
                "editorial_html": NEAR,
                "content_html": NEAR + BOILERPLATE,
            },
        )

        write_json(root / "radar_tech_br/data/publication_history.json", {"items": []})
        write_json(root / "radar_tech_br/data/editorial_queue.json", {"items": []})

        write_json(
            root / "casa_decoracao/data/editorial_queue.json",
            {
                "items": [
                    {"id": 1, "shopee_item_id": "CASA-1", "status": "GENERATED"},
                    {"id": 2, "shopee_item_id": "CASA-2", "status": "GENERATED"},
                ]
            },
        )
        write_json(
            root / "casa_decoracao/data/generated/001.json",
            {
                "id": 1,
                "shopee_item_id": "CASA-1",
                "status": "GENERATED",
                "editorial_title": "Organize sua bancada",
                "editorial_html": BASE,
                "content_html": BASE + BOILERPLATE,
            },
        )
        write_json(
            root / "casa_decoracao/data/generated/002.json",
            {
                "id": 2,
                "shopee_item_id": "CASA-2",
                "status": "GENERATED",
                "editorial_title": "Iluminação para sala pequena",
                "editorial_html": DISTINCT,
                "content_html": DISTINCT + BOILERPLATE,
            },
        )

        report = run_guard(root, "casa_decoracao", mutate=True)
        assert report["blocked"] == 1, report
        assert report["passed"] == 1, report

        queue = json.loads(
            (root / "casa_decoracao/data/editorial_queue.json").read_text(
                encoding="utf-8"
            )
        )
        by_id = {int(item["id"]): item for item in queue["items"]}
        assert by_id[1]["status"] == "BLOCKED", by_id[1]
        assert str(by_id[1]["last_error"]).startswith("cross_blog_guard:"), by_id[1]
        assert by_id[2]["status"] == "GENERATED", by_id[2]

        saved_report = json.loads(
            (root / "casa_decoracao/data/cross_blog_guard_report.json").read_text(
                encoding="utf-8"
            )
        )
        assert saved_report["blocked"] == 1
        assert saved_report["passed"] == 1


def main() -> int:
    pure_similarity_tests()
    integration_test()
    print("editorial_cross_blog_guard_self_test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
