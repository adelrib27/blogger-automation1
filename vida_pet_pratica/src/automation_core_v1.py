import hashlib
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROOT_SRC = ROOT / "src"
LAB_ROOT = ROOT / "vida_pet_pratica"
POLICY_PATH = LAB_ROOT / "config" / "automation_policy.json"
STATE_DIR = LAB_ROOT / "state"
OUT_DIR = LAB_ROOT / "data" / "architecture_lab"

os.environ["SHOPEE_OPPORTUNITIES_CONFIG"] = str(LAB_ROOT / "config" / "shopee_oportunidades.json")
os.environ["SHOPEE_INTENT_RULES"] = str(LAB_ROOT / "config" / "shopee_intent_rules.json")
os.environ["SHOPEE_OUTPUT_DIR"] = str(LAB_ROOT / "data" / "shopee_oportunidades")
os.environ.setdefault("SHOPEE_TOP_N", "24")

if str(ROOT_SRC) not in sys.path:
    sys.path.insert(0, str(ROOT_SRC))
if str(LAB_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(LAB_ROOT / "src"))

import shopee_oportunidades_v23 as shopee  # noqa: E402
import evidence_engine as evidence  # noqa: E402

ANGLE_LIBRARY = {
    "Conforto": [
        "como escolher conforto sem exagerar nas promessas",
        "onde posicionar o acessório no dia a dia",
        "critérios práticos para comparar opções",
        "rotina de limpeza e conservação",
        "erros comuns na escolha do acessório",
    ],
    "Alimentacao e Hidratacao": [
        "como escolher o acessório conforme o porte e a rotina",
        "organização do cantinho de alimentação",
        "higiene e manutenção do acessório",
        "critérios para comparar formatos e usos",
        "erros comuns na organização da alimentação",
    ],
    "Higiene": [
        "como organizar uma rotina de higiene mais prática",
        "onde posicionar o acessório para facilitar a limpeza",
        "critérios para comparar opções de higiene",
        "como manter o espaço do pet mais organizado",
        "erros comuns que aumentam a sujeira no ambiente",
    ],
    "Diversao e Enriquecimento": [
        "como variar a rotina de brincadeiras com supervisão",
        "critérios para escolher atividades adequadas ao pet",
        "como organizar momentos curtos de interação",
        "erros comuns ao escolher brinquedos e acessórios",
        "como alternar estímulos sem depender de um único brinquedo",
    ],
    "Transporte e Passeio": [
        "como conferir ajuste e compatibilidade antes do uso",
        "checklist de preparação para passeios e deslocamentos",
        "critérios práticos para comparar acessórios",
        "cuidados de supervisão durante o uso",
        "erros comuns na escolha de acessórios de passeio",
    ],
    "Organizacao": [
        "como organizar os acessórios do pet em pouco espaço",
        "como reduzir bagunça na rotina diária",
        "critérios para escolher organizadores funcionais",
        "rotina simples de manutenção e limpeza",
        "erros comuns ao guardar itens do pet",
    ],
}


def load_json(path: Path, default):
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def fingerprint(product_id: str, angle: str) -> str:
    return hashlib.sha256(f"{product_id}|{evidence.normalize(angle)}".encode("utf-8")).hexdigest()[:20]


def source_guard(item: dict) -> tuple[bool, list[str]]:
    name = evidence.normalize(item.get("productName") or "")
    blocked_terms = [
        "medicamento", "remedio", "antibiotico", "anti inflamatorio", "vermifugo",
        "antipulgas", "carrapaticida", "suplemento", "vitamina", "shampoo medicamentoso",
        "tratamento veterinario", "racao seca", "racao umida", "sache", "petisco", "alimento completo",
    ]
    hits = [term for term in blocked_terms if evidence.normalize(term) in name]
    return not hits, hits


def pet_regression_checks(rules_doc):
    cases = [
        ("Cama Pet Lavável para Cachorro e Gato", "cama pet", True),
        ("Cama Infantil Montessoriana Solteiro", "cama pet", False),
        ("Fonte Bebedouro Automático para Gatos", "bebedouro fonte pet", True),
        ("Bebedouro para Pássaros de Gaiola", "bebedouro fonte pet", False),
        ("Tapete Higiênico para Cachorro Pet", "tapete higienico cachorro", True),
        ("Tapete Higiênico para Banheiro Antiderrapante", "tapete higienico cachorro", False),
        ("Caixa Bandeja de Areia para Gatos", "caixa areia gato", True),
        ("Caixa Organizadora com Areia Decorativa", "caixa areia gato", False),
        ("Brinquedo Interativo Pet para Cachorro", "brinquedo interativo pet", True),
        ("Brinquedo Interativo Infantil Educativo", "brinquedo interativo pet", False),
        ("Arranhador para Gatos com Base", "arranhador gato", True),
        ("Peitoral Ajustável para Cachorro Pet", "peitoral cachorro", True),
        ("Peitoral Esportivo Humano Academia", "peitoral cachorro", False),
        ("Guia Retrátil para Cachorro Pet", "guia cachorro", True),
        ("Guia Turístico de Viagem", "guia cachorro", False),
        ("Recipiente Porta Ração Pet", "porta racao pet", True),
    ]
    failures = []
    for title, keyword, expected in cases:
        actual = bool(shopee.evaluate_keyword(title, keyword, rules_doc).get("accepted"))
        if actual != expected:
            failures.append({"title": title, "keyword": keyword, "expected": expected, "actual": actual})
    if failures:
        raise SystemExit("Falha nos testes semânticos Vida Pet Prática: " + json.dumps(failures, ensure_ascii=False))
    print(f"Testes semânticos Vida Pet Prática: {len(cases)}/{len(cases)} OK")


def choose_angle(item: dict, history: list[dict], max_similarity: float) -> tuple[str | None, str]:
    category = str((item.get("categories") or ["Organizacao"])[0])
    candidates = ANGLE_LIBRARY.get(category) or ANGLE_LIBRARY["Organizacao"]
    product_id = str(item.get("itemId") or "")
    prior = [h for h in history if str(h.get("itemId") or "") == product_id]
    old_texts = [str(h.get("angle") or "") for h in prior] + [str(h.get("title") or "") for h in prior]
    for angle in candidates:
        if any(evidence.similarity(angle, old) >= max_similarity for old in old_texts if old):
            continue
        return angle, "NEW_ANGLE"
    return None, "ANGLES_EXHAUSTED"


def is_product_recent(item_id: str, history: list[dict], cooldown_days: int) -> bool:
    cutoff = int(time.time()) - cooldown_days * 86400
    return any(str(row.get("itemId") or "") == item_id and int(row.get("publishedAt") or 0) >= cutoff for row in history)


def main():
    policy = load_json(POLICY_PATH, {})
    min_ready = int(policy.get("min_ready", 3))
    attempt_limit = int(policy.get("candidate_attempt_limit", 20))
    max_similarity = float((policy.get("anti_duplicate") or {}).get("max_similarity", 0.72))
    cooldown_days = int((policy.get("rotation") or {}).get("product_cooldown_days", 30))
    max_results = int((policy.get("evidence") or {}).get("max_search_results", 8))

    if (policy.get("wordpress") or {}).get("writes_enabled") is not False:
        raise SystemExit("SAFE bloqueado: wordpress.writes_enabled precisa ser false no laboratório")

    history = load_json(STATE_DIR / "article_history.json", [])
    if not isinstance(history, list):
        raise SystemExit("article_history.json inválido")

    shopee.run_regression_checks = pet_regression_checks
    ranking = shopee.scan_v23()
    ready, rejected = [], []
    attempts = 0
    evidence_dir = OUT_DIR / "evidence"

    for item in ranking:
        if attempts >= attempt_limit or len(ready) >= min_ready:
            break
        attempts += 1
        item_id = str(item.get("itemId") or "")
        allowed, blocked = source_guard(item)
        if not allowed:
            rejected.append({"itemId": item_id, "stage": "SOURCE_GUARD", "reasons": blocked})
            continue
        if is_product_recent(item_id, history, cooldown_days):
            rejected.append({"itemId": item_id, "stage": "PRODUCT_COOLDOWN", "reasons": [f"cooldown_days:{cooldown_days}"]})
            continue
        try:
            package = evidence.build_evidence_package(item, max_results=max_results)
        except Exception as exc:
            rejected.append({"itemId": item_id, "stage": "EVIDENCE_ENGINE", "reasons": [str(exc)]})
            continue
        save_json(evidence_dir / f"{item_id}.json", package)
        if package.get("status") != "VERIFIED":
            rejected.append({"itemId": item_id, "stage": "EVIDENCE_REJECTED", "reasons": package.get("reasons") or []})
            continue
        angle, angle_status = choose_angle(item, history, max_similarity)
        if not angle:
            rejected.append({"itemId": item_id, "stage": angle_status, "reasons": ["no_unique_angle_available"]})
            continue
        ready.append({
            "status": "VERIFIED_READY_CANDIDATE",
            "itemId": item_id,
            "productName": item.get("productName"),
            "category": (item.get("categories") or [None])[0],
            "keyword": (item.get("intentMatchedKeywords") or item.get("keywords") or [None])[0],
            "angle": angle,
            "angle_status": angle_status,
            "fingerprint": fingerprint(item_id, angle),
            "evidence_file": f"evidence/{item_id}.json",
            "authorized_evidence_ids": package.get("authorized_evidence_ids") or [],
        })

    mode = "NEW_PRODUCT_DISCOVERY"
    if len(ready) < min_ready:
        mode = "EVERGREEN_ROTATION_FALLBACK"
        known = {}
        for row in history:
            if str(row.get("evidenceStatus") or "") == "VERIFIED" and row.get("itemId"):
                known[str(row["itemId"])] = row
        for item_id, row in known.items():
            if len(ready) >= min_ready:
                break
            if any(x["itemId"] == item_id for x in ready):
                continue
            pseudo = {
                "itemId": item_id,
                "productName": row.get("productName"),
                "categories": [row.get("category") or "Organizacao"],
                "intentMatchedKeywords": [row.get("keyword") or "pet"],
            }
            angle, angle_status = choose_angle(pseudo, history, max_similarity)
            if not angle:
                continue
            ready.append({
                "status": "EVERGREEN_READY_CANDIDATE",
                "itemId": item_id,
                "productName": row.get("productName"),
                "category": row.get("category"),
                "keyword": row.get("keyword"),
                "angle": angle,
                "angle_status": angle_status,
                "fingerprint": fingerprint(item_id, angle),
                "evidence_file": row.get("evidenceFile"),
                "authorized_evidence_ids": row.get("authorizedEvidenceIds") or [],
            })

    health = "HEALTHY" if len(ready) >= min_ready else ("ATTENTION" if ready else "EMERGENCY")
    report = {
        "status": "ARCHITECTURE_LAB_COMPLETE",
        "version": "VIDA_PET_AUTOMATION_CORE_V1",
        "wordpress_written": False,
        "publishing_enabled": False,
        "min_ready": min_ready,
        "ready_count": len(ready),
        "buffer_health": health,
        "mode": mode,
        "candidate_attempts": attempts,
        "candidate_rejections": len(rejected),
        "firecrawl_auth_mode": "API_KEY" if os.getenv("FIRECRAWL_API_KEY", "").strip() else "KEYLESS_LAB",
        "ready_buffer": ready,
        "rejections": rejected,
        "guards": {
            "candidate_failover": True,
            "evidence_fail_closed": True,
            "similar_product_specs_blocked": True,
            "evergreen_rotation": True,
            "anti_duplicate_angle_guard": True,
            "wordpress_write_blocked": True,
        },
    }
    save_json(OUT_DIR / "ready_buffer.json", ready)
    save_json(OUT_DIR / "candidate_rejections.json", rejected)
    save_json(OUT_DIR / "architecture_report.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not ready:
        raise SystemExit("Nenhum candidato VERIFIED_READY foi produzido; revisar fontes/evidências")


if __name__ == "__main__":
    main()
