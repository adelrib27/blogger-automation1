"""Validador somente leitura do inventário de credenciais V31 Editorial.

Não consulta APIs, não faz download dos feeds, não imprime valores.
Executar: python -m affiliate_hub_v31.credentials --profile shopee
"""
from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path

REGISTRY = Path(__file__).with_name("credentials_registry.json")
PROFILES = ("manifest", "shopee", "feeds", "storage", "all")
VALID_TYPES = {"secret", "variable"}
VALID_SECTIONS = {"shopee", "feeds", "storage"}


def load_registry(path: Path = REGISTRY) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1 or data.get("namespace") != "V31_EDITORIAL_":
        raise ValueError("Versão/namespace incompatível")
    credentials = data.get("credentials")
    if not isinstance(credentials, list) or not credentials:
        raise ValueError("Registro de credenciais vazio/inválido")
    seen = set()
    for entry in credentials:
        if not isinstance(entry, dict):
            raise ValueError("Entrada inválida no registro")
        if set(entry) != {"name", "type", "profile", "purpose"}:
            raise ValueError("Campo inesperado no registro (nunca incluir valores)")
        name = entry.get("name")
        if not isinstance(name, str) or not re.fullmatch(r"V31_EDITORIAL_[A-Z0-9_]+", name):
            raise ValueError("Nome de credencial inválido")
        if name in seen:
            raise ValueError("Credencial duplicada")
        seen.add(name)
        if entry.get("type") not in VALID_TYPES or entry.get("profile") not in VALID_SECTIONS:
            raise ValueError("Tipo ou perfil inválido")
        if not isinstance(entry.get("purpose"), str) or not entry["purpose"].strip():
            raise ValueError("Descrição ausente")
    return data


def check_presence(profile: str, env: dict[str, str] | None = None, path: Path = REGISTRY) -> list[tuple[str, str, bool]]:
    if profile not in PROFILES:
        raise ValueError("Perfil inválido")
    data = load_registry(path)
    env = os.environ if env is None else env
    if profile == "manifest":
        return []
    entries = data["credentials"]
    selected = entries if profile == "all" else [e for e in entries if e["profile"] == profile]
    return [(item["name"], item["type"], bool(str(env.get(item["name"], "")).strip())) for item in selected]


def main() -> int:
    parser = argparse.ArgumentParser(description="Verificar presença de secrets/variables sem exibir valores")
    parser.add_argument("--profile", choices=PROFILES, default="manifest")
    args = parser.parse_args()
    try:
        statuses = check_presence(args.profile)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        # Não imprimir detalhes de falha em arquivos arbitrários ou variáveis.
        print(f"V31_CREDENTIALS_REGISTRY_INVALID ({type(exc).__name__})")
        return 3
    if args.profile == "manifest":
        print("V31_CREDENTIALS_MANIFEST_VALID")
        return 0
    for name, kind, present in statuses:
        print(f"{'PRESENTE' if present else 'AUSENTE'}: {name} ({kind})")
    missing = sum(not present for _, _, present in statuses)
    print(f"V31_CREDENTIALS_{'READY' if missing == 0 else 'INCOMPLETE'}: {len(statuses) - missing}/{len(statuses)}")
    return 0 if missing == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
