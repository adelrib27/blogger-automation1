#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SELECTION_PATH = ROOT / "radar_tech_br" / "data" / "store_last_selection.json"
RANKING_PATH = ROOT / "radar_tech_br" / "data" / "store_shopee_scan" / "ranking.json"
ENDPOINT = os.getenv("SHOPEE_AFFILIATE_ENDPOINT", "https://open-api.affiliate.shopee.com.br/graphql").strip()
EXPECTED_APP_ID = "18352820579"


def required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Variável obrigatória ausente: {name}")
    return value


def auth_header(app_id: str, secret: str, payload: str, timestamp: int) -> str:
    raw = f"{app_id}{timestamp}{payload}{secret}"
    signature = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return f"SHA256 Credential={app_id}, Timestamp={timestamp}, Signature={signature}"


def post_graphql(app_id: str, secret: str, payload_obj: dict) -> dict:
    payload = json.dumps(payload_obj, ensure_ascii=False, separators=(",", ":"))
    timestamp = int(time.time())
    req = urllib.request.Request(
        ENDPOINT,
        data=payload.encode("utf-8"),
        method="POST",
        headers={
            "Authorization": auth_header(app_id, secret, payload, timestamp),
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "BloggerStore-ShopeeLinkValidator/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=35) as response:
            return json.loads(response.read().decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Shopee HTTP {exc.code}: {body[:500]}") from exc


def generate_short_link(app_id: str, secret: str, origin_url: str) -> str:
    query = (
        "mutation GenerateShortLink($originUrl: String!, $subIds: [String!]) { "
        "generateShortLink(input: {originUrl: $originUrl, subIds: $subIds}) { shortLink } "
        "}"
    )
    result = post_graphql(
        app_id,
        secret,
        {
            "query": query,
            "variables": {"originUrl": origin_url, "subIds": []},
            "operationName": "GenerateShortLink",
        },
    )
    errors = result.get("errors") or []
    if errors:
        safe = [{"code": (e.get("extensions") or {}).get("code"), "message": e.get("message")} for e in errors[:3]]
        raise RuntimeError(f"generateShortLink retornou erro: {json.dumps(safe, ensure_ascii=False)}")
    link = str((((result.get("data") or {}).get("generateShortLink") or {}).get("shortLink") or "")).strip()
    if not link.startswith("https://"):
        raise RuntimeError("generateShortLink não retornou URL HTTPS.")
    return link


def resolved_to_shopee(short_link: str) -> tuple[bool, str, int | None]:
    req = urllib.request.Request(
        short_link,
        method="GET",
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/156 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
    )
    final_url = short_link
    status = None
    try:
        with urllib.request.urlopen(req, timeout=25) as response:
            final_url = response.geturl()
            status = getattr(response, "status", None)
    except urllib.error.HTTPError as exc:
        # A página final pode recusar o runner (403/429) mesmo depois de o encurtador
        # ter redirecionado corretamente. Nesse caso, o destino final ainda é evidência útil.
        final_url = exc.geturl() or short_link
        status = exc.code
    except Exception as exc:
        return False, f"ERRO:{type(exc).__name__}:{exc}", None

    parsed_short = urllib.parse.urlparse(short_link)
    parsed_final = urllib.parse.urlparse(final_url)
    host = (parsed_final.hostname or "").lower()
    redirected = final_url.rstrip("/") != short_link.rstrip("/")
    shopee_host = host == "shopee.com.br" or host.endswith(".shopee.com.br")
    still_shortener = (parsed_final.hostname or "").lower() == (parsed_short.hostname or "").lower() and parsed_final.path == parsed_short.path
    return bool(redirected and shopee_host and not still_shortener), final_url, status


def load_ranking_by_item() -> dict[str, dict]:
    if not RANKING_PATH.exists():
        raise RuntimeError(f"Ranking da coleta não encontrado: {RANKING_PATH}")
    data = json.loads(RANKING_PATH.read_text(encoding="utf-8"))
    ranking = data.get("ranking") if isinstance(data, dict) else None
    if not isinstance(ranking, list):
        raise RuntimeError("Formato inesperado de ranking.json")
    return {str(item.get("itemId") or "").strip(): item for item in ranking if str(item.get("itemId") or "").strip()}


def main() -> int:
    app_id = required_env("SHOPEE_APP_ID")
    secret = required_env("SHOPEE_SECRET")
    if app_id != EXPECTED_APP_ID:
        raise RuntimeError("SHOPEE_APP_ID não corresponde ao AppID autorizado esperado.")
    if not SELECTION_PATH.exists():
        raise RuntimeError("store_last_selection.json não encontrado.")

    selection = json.loads(SELECTION_PATH.read_text(encoding="utf-8"))
    if selection.get("status") != "PUBLISHED" or selection.get("dryRun") is not False:
        raise RuntimeError("Seleção não está em estado PUBLISHED/dryRun=false.")

    ranking_by_item = load_ranking_by_item()
    categories = selection.get("categories") or {}
    items = [item for values in categories.values() for item in (values or [])]
    if len(items) != 20 or len(categories) != 5:
        raise RuntimeError(f"Seleção inválida: categorias={len(categories)} itens={len(items)}")

    generated: dict[str, dict] = {}
    for index, item in enumerate(items, start=1):
        item_id = str(item.get("itemId") or "").strip()
        ranked = ranking_by_item.get(item_id) or {}
        origin = str(ranked.get("productLink") or "").strip()
        if not origin.startswith("http"):
            raise RuntimeError(f"Produto {item_id} sem productLink original no ranking.")

        short = generate_short_link(app_id, secret, origin)
        ok, final_url, status = resolved_to_shopee(short)
        if not ok:
            raise RuntimeError(
                f"Link afiliado não resolveu para página Shopee: item={item_id} short={short} final={final_url} status={status}"
            )

        item["offerLink"] = short
        generated[item_id] = {"shortLink": short, "resolvedUrl": final_url, "httpStatus": status}
        print(f"[{index:02d}/20] item {item_id}: link gerado e destino Shopee validado.")
        time.sleep(0.15)

    if len(generated) != 20:
        raise RuntimeError(f"Validação incompleta: {len(generated)}/20 links.")

    selection["affiliateLinkGeneration"] = {
        "method": "generateShortLink",
        "appId": EXPECTED_APP_ID,
        "validatedCount": 20,
        "allResolvedToShopee": True,
        "validatedAtUnix": int(time.time()),
    }
    SELECTION_PATH.write_text(json.dumps(selection, ensure_ascii=False, indent=2), encoding="utf-8")
    print("LINK_VALIDATION_OK: 20/20 links gerados via generateShortLink e resolvidos para Shopee.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"LINK_VALIDATION_FAILED: {exc}", file=sys.stderr)
        raise
