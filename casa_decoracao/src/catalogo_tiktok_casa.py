import json
import re
import unicodedata
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "casa_decoracao" / "config" / "catalogo_tiktok.json"


def normalize(text: str) -> str:
    value = unicodedata.normalize("NFKD", str(text or "").casefold())
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    config = load_json(CONFIG_PATH)
    source = ROOT / config["source"]
    output = ROOT / config["output"]
    products = load_json(source)

    include = [normalize(x) for x in config.get("include_any", [])]
    exclude = [normalize(x) for x in config.get("exclude_any", [])]

    selected = []
    rejected = []

    for product in products:
        if not isinstance(product, dict) or not product.get("ativo", False):
            continue
        name = str(product.get("nome") or "").strip()
        link = str(product.get("link_afiliado") or "").strip()
        normalized = normalize(name)
        if not name or not link:
            continue

        blocked = next((term for term in exclude if term and term in normalized), None)
        matched = [term for term in include if term and term in normalized]

        if blocked or not matched:
            rejected.append({"nome": name, "blocked": blocked, "matched": matched})
            continue

        selected.append({
            "nome": name,
            "link_afiliado": link,
            "ativo": True,
            "origem": "TikTok Shop",
            "matched_terms": matched,
        })

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(selected, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    report = output.with_name("tiktok_catalog_report.json")
    report.write_text(
        json.dumps(
            {
                "source": str(source.relative_to(ROOT)),
                "selected": len(selected),
                "rejected": len(rejected),
                "products": selected,
                "rejected_sample": rejected[:30],
            },
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )

    print(f"Casa e Decoracao — produtos TikTok selecionados: {len(selected)}")
    print(f"Saida: {output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
