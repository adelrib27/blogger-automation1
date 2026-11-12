#!/usr/bin/env python3
"""V31 LAB — comissao positiva + rotacao por esgotamento comprovado.

Contrato deliberadamente conservador: productOfferV2 nao comprova estoque por
ausencia de item. Sinais de estoque so podem vir de adaptador autenticado e
homologado, com observacoes independentes. Nenhuma chamada HTTP / PUT Blogger.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

from replication_safe import GateError
from shopee_r2_safe import KEYWORDS, REQUIRED, normalize, choose, render

INVENTORY_SOURCE = "shopee_authorized_inventory"
OOS = "CONFIRMED_OUT_OF_STOCK"
IN_STOCK = "IN_STOCK"
UNKNOWN = "UNKNOWN"
MIN_SEPARATION = timedelta(minutes=15)
MAX_AGE = timedelta(hours=24)


def _decimal(value: Any) -> Decimal | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        value = Decimal(str(value))
        return value if value.is_finite() else None
    except (InvalidOperation, ValueError, TypeError):
        return None


def commission_eligible(raw: dict, *, verified_affiliate_response: bool) -> bool:
    """Sem percentual minimo. Verifica comissao TOTAL positiva da conta.

    Nao soma taxas base + seller: o modelo da API pode ja retornar o total.
    Nao exige sellerCommissionRate/extra. Ausencia de dado = UNKNOWN, nao elegivel.
    A prova de origem deve vir do gateway autenticado, nunca de entrada de publico.
    """
    if not verified_affiliate_response or not isinstance(raw, dict):
        return False
    rate = _decimal(raw.get("commissionRate"))
    absolute = _decimal(raw.get("commission"))
    # Valor explicito de comissao zero e taxa positiva criam conflito; nao confiar.
    if (rate is not None and rate < 0) or (absolute is not None and absolute < 0):
        return False
    if rate is not None and absolute is not None and ((rate > 0) != (absolute > 0)):
        return False
    return (rate is not None and rate > 0) or (absolute is not None and absolute > 0)


def _utc(raw: object) -> datetime | None:
    if not isinstance(raw, str):
        return None
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return dt.astimezone(timezone.utc) if dt.tzinfo else None
    except ValueError:
        return None


def classify_product_offer_visibility(item_id: str, payload: object, *,
                                      http_status: int | None = 200) -> dict:
    """A busca productOfferV2 NÃO informa estoque de forma homologada.

    Resultado ausente, erro 10000, HTTP 200 + GraphQL errors, estoque nulo e
    campos 'stock' hipotéticos NUNCA são convertidos em zero/disponibilidade.
    A disponibilidade fica UNKNOWN, mesmo quando o item aparece na busca.
    Apenas um adaptador de estoque autorizado, separado, pode comprovar OOS.
    """
    if not isinstance(item_id, str) or not item_id.isdigit():
        raise GateError("INVALID_DISCOVERY_ITEM_ID")
    base = {"stock_status": UNKNOWN, "stock_source": "NO_VERIFIED_INVENTORY"}
    if http_status != 200 or not isinstance(payload, dict):
        return {**base, "discovery_status": "API_UNAVAILABLE"}
    if payload.get("errors"):
        return {**base, "discovery_status": "API_GRAPHQL_ERROR"}
    data = payload.get("data")
    offers = data.get("productOfferV2") if isinstance(data, dict) else None
    nodes = offers.get("nodes") if isinstance(offers, dict) else None
    if not isinstance(nodes, list):
        return {**base, "discovery_status": "INVALID_DISCOVERY"}
    listed = any(isinstance(row, dict) and
                 str(row.get("itemId") or "").strip() == item_id for row in nodes)
    return {**base, "discovery_status": "LISTED" if listed else "NOT_LISTED"}


def require_clean_discovery_metadata(metadata: object) -> None:
    """Guard SAFE do envelope da lista de candidatos da Loja.

    É contrato de dados, NÃO autenticação: um JSON arbitrário não prova que
    veio da Shopee. Mesmo com metadados válidos, nunca permite PUT.
    """
    if not isinstance(metadata, dict):
        raise GateError("DISCOVERY_METADATA_MISSING")
    if (metadata.get("operation") != "productOfferV2" or
        metadata.get("http_status") != 200 or
        metadata.get("query_status") != "OK" or
        metadata.get("graphql_error_codes") != []):
        raise GateError("DISCOVERY_NOT_CLEAN_NO_ROTATION")


def stock_status(item_id: str, observations: list[dict], *, now: datetime) -> str:
    """Estoque desconhecido salvo prova explicita com duas leituras independentes.

    Dois '0' da mesma execução nao comprovam esgotamento. Resposta API com erro,
    pagina indisponivel, item ausente da busca e stock nulo nunca comprovam 0.
    O adaptador autorizado deve assinar/validar a origem ANTES de fornecer dados.
    """
    if not isinstance(item_id, str) or not item_id.isdigit():
        raise GateError("INVALID_STOCK_ITEM_ID")
    if not isinstance(observations, list) or now.tzinfo is None:
        raise GateError("INVALID_STOCK_OBSERVATIONS")
    reference = now.astimezone(timezone.utc)
    validated = []
    latest_unknown = None
    for raw in observations:
        if not isinstance(raw, dict) or str(raw.get("item_id")) != item_id:
            continue
        dt = _utc(raw.get("observed_at"))
        if dt is None or dt > reference or reference - dt > MAX_AGE:
            continue
        # So aceitamos UMA fonte homologada; validacao de origem e externa.
        success = (raw.get("source") == INVENTORY_SOURCE and
                   raw.get("authenticated") is True and
                   raw.get("success") is True and
                   isinstance(raw.get("run_id"), str) and
                   4 <= len(raw["run_id"]) <= 100)
        qty = raw.get("stock_units")
        if not success or type(qty) is not int or qty < 0:
            if latest_unknown is None or dt > latest_unknown:
                latest_unknown = dt
            continue
        validated.append((dt, raw["run_id"], qty))
    if not validated:
        return UNKNOWN
    validated.sort(key=lambda p: p[0])
    latest_time, latest_run, latest_qty = validated[-1]
    # Observacao mais nova sem prova valida invalida confirmacao antiga.
    if latest_unknown is not None and latest_unknown >= latest_time:
        return UNKNOWN
    if latest_qty > 0:
        return IN_STOCK
    for earlier_time, earlier_run, earlier_qty in reversed(validated[:-1]):
        if earlier_qty > 0:
            # Uma leitura com estoque apos um zero anterior impede confirmacao.
            return UNKNOWN
        if earlier_qty == 0 and earlier_run != latest_run and (
                latest_time - earlier_time >= MIN_SEPARATION):
            return OOS
    return UNKNOWN


def select_verified(profile: dict, offers: dict[str, list[dict]], *,
                    observations: list[dict] | None = None,
                    now: datetime | None = None) -> list[dict]:
    """Selecao comercial em LAB. Mantem 16 produtos, dedup e criterio semantico."""
    now = now or datetime.now(timezone.utc)
    observations = observations or []
    categories = profile["store"]["categories"]
    if set(offers) != {c["name"] for c in categories}:
        raise GateError("CATEGORY_PROFILE_MISMATCH")
    filtered = {}
    for category in categories:
        name = category["name"]
        filtered[name] = [
            row for row in offers[name]
            if isinstance(row, dict)
            and commission_eligible(row, verified_affiliate_response=True)
            and stock_status(str(row.get("itemId", "")), observations, now=now) != OOS
        ]
    return choose(profile, filtered)


def plan_oos_rotation(current: list[dict], offers: dict[str, list[dict]],
                      observations: list[dict], *, now: datetime) -> dict:
    """Troca somente OOS confirmado por alternativo elegivel, sem efetuar PUT.

    Ausencia de oferta, conflito ou origem de estoque nao validada bloqueia a
    rotacao. Nao retira produtos apenas para simular renovacao.
    """
    if len(current) != REQUIRED or len({p.get("item_id") for p in current}) != REQUIRED:
        raise GateError("CURRENT_STORE_NOT_16_UNIQUE")
    counts = Counter(p.get("category") for p in current)
    if set(counts) != set(KEYWORDS) or any(v != 4 for v in counts.values()):
        raise GateError("CURRENT_STORE_CATEGORY_MISMATCH")
    if set(offers) != set(KEYWORDS):
        raise GateError("CANDIDATE_CATEGORIES_MISMATCH")
    for product in current:
        if not isinstance(product.get("item_id"), str) or not product["item_id"].isdigit():
            raise GateError("CURRENT_STORE_ITEM_INVALID")
    oos_slots = [
        i for i, p in enumerate(current)
        if stock_status(p["item_id"], observations, now=now) == OOS
    ]
    if not oos_slots:
        return {"status": "NO_CONFIRMED_STOCK_CHANGE", "writes": False,
                "new_item_count": 0, "stock_replacements": 0, "products": current}
    proposed = [dict(p) for p in current]
    occupied = {p["item_id"] for p in current}
    # Mais de um OOS pode ser trocado numa mesma proposta, mantendo 4/categoria.
    for index in oos_slots:
        category = current[index]["category"]
        replacement = None
        for raw in offers[category]:
            if not isinstance(raw, dict) or not commission_eligible(raw, verified_affiliate_response=True):
                continue
            item = normalize(raw, category)
            if item is None or item["item_id"] in occupied:
                continue
            if stock_status(item["item_id"], observations, now=now) == OOS:
                continue
            replacement = item
            break
        if replacement is None:
            return {"status": "BLOCK_NO_VERIFIED_REPLACEMENT", "writes": False,
                    "new_item_count": 0, "stock_replacements": 0, "products": current}
        occupied.add(replacement["item_id"])
        proposed[index] = replacement
    if len({p["item_id"] for p in proposed}) != REQUIRED:
        raise GateError("DUPLICATE_ROTATED_ITEM")
    # Reusa renderer V31 e seus guardas de cards/links.
    candidate_html = render(proposed, lab_url="https://lab.invalid/")
    if candidate_html.count('class="ub-product-card"') != REQUIRED:
        raise GateError("ROTATED_HTML_INVALID")
    return {"status": "OOS_REPLACEMENT_CANDIDATE_SAFE_REVIEW", "writes": False,
            "new_item_count": len(oos_slots), "stock_replacements": len(oos_slots),
            "products": proposed, "candidate_html": candidate_html}


def run_lab_cli(argv: list[str] | None = None) -> int:
    """Planeja alteracao em artefatos separados. NUNCA escreve no Blogger.

    Dados de estoque e comissao devem ser preparados por adaptadores
    autenticados e auditados; os marcadores em arquivos JSON nao provam sua
    origem. Portanto o resultado sera SEMPRE um candidato LAB SAFE.
    """
    import argparse
    import json
    from pathlib import Path
    from replication_safe import load_profile

    parser = argparse.ArgumentParser(description="Loja V31: plano SAFE de estoque/comissao")
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--current", type=Path, required=True)
    parser.add_argument("--offers", type=Path, required=True)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args(argv)

    try:
        profile = load_profile(args.profile)
        if profile.get("mode") != "LAB_SAFE_ONLY":
            raise GateError("ONLY_LAB_PROFILE_ALLOWED")
        target = str(profile["target"]["blog_id"])
        # Nunca misturar dados de outros blogs (mesmo que todos sejam LAB).
        current = json.loads(args.current.read_text(encoding="utf-8"))
        candidates = json.loads(args.offers.read_text(encoding="utf-8"))
        inventory = json.loads(args.inventory.read_text(encoding="utf-8"))
        if not all(isinstance(x, dict) and str(x.get("blog_id")) == target
                   for x in (current, candidates, inventory)):
            raise GateError("CROSS_BLOG_INPUT_DENIED")
        if current.get("count") != REQUIRED or not isinstance(current.get("products"), list):
            raise GateError("CURRENT_CATALOG_INVALID")
        if not isinstance(candidates.get("categories"), dict):
            raise GateError("CANDIDATE_CATALOG_INVALID")
        require_clean_discovery_metadata(candidates.get("discovery"))
        if not isinstance(inventory.get("observations"), list):
            raise GateError("INVENTORY_FORMAT_INVALID")
        result = plan_oos_rotation(current["products"], candidates["categories"],
                                   inventory["observations"], now=datetime.now(timezone.utc))
        status = result["status"]
        summary = {"status": status, "writes_blogger": False, "lab_only": True,
                   "new_item_count": result["new_item_count"],
                   "stock_replacements": result["stock_replacements"],
                   "target_blog_id": target}
        if status != "OOS_REPLACEMENT_CANDIDATE_SAFE_REVIEW":
            print(json.dumps(summary, ensure_ascii=False))
            return 0
        if args.out_dir.exists():
            raise GateError("OUTPUT_DIRECTORY_ALREADY_EXISTS")
        args.out_dir.mkdir(parents=True, exist_ok=False)
        (args.out_dir / "loja_candidata_safe.html").write_text(
            result["candidate_html"], encoding="utf-8")
        (args.out_dir / "loja_plano_safe.json").write_text(
            json.dumps({"summary": summary, "products": result["products"]},
                       ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(summary, ensure_ascii=False))
        return 0
    except (GateError, OSError, ValueError, KeyError, TypeError) as exc:
        # Somente o tipo e um status fixo; nao ecoar caminhos ou dados sensiveis.
        print(json.dumps({"status": "STOCK_ROTATION_LAB_FAIL_CLOSED",
                          "error_type": type(exc).__name__, "writes_blogger": False}))
        return 2


if __name__ == "__main__":
    raise SystemExit(run_lab_cli())
