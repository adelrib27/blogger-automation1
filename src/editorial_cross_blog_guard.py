#!/usr/bin/env python3
"""Gate anti-repetição editorial entre projetos.

Compara apenas ``editorial_html`` — nunca o ``content_html`` completo — para
que CTA, aviso de afiliado, elementos legais e layout compartilhado não gerem
falso positivo.

Comportamento de produção:
- examina candidatos com status GENERATED no projeto alvo;
- compara com material publicado/gerado dos outros projetos configurados;
- bloqueia somente colisões de alta confiança, marcando o item como BLOCKED;
- grava relatório legível por máquina em data/cross_blog_guard_report.json;
- conclui com sucesso após a varredura, mesmo se algum item for bloqueado, para
  permitir que o publicador existente tente o próximo candidato limpo.

Erros de configuração/operação falham a execução.
"""
from __future__ import annotations

import argparse
import html
import json
import math
import re
import unicodedata
from collections import Counter
from dataclasses import asdict, dataclass
from difflib import SequenceMatcher
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

DEFAULT_CONFIG = Path("config/editorial_cross_blog_guard.json")

STOPWORDS = {
    "a", "ao", "aos", "aquela", "aquele", "aqueles", "as", "ate", "com", "como",
    "da", "das", "de", "dela", "dele", "deles", "do", "dos", "e", "ela", "elas",
    "ele", "eles", "em", "entre", "era", "essa", "esse", "esta", "este", "eu",
    "foi", "ha", "isso", "isto", "ja", "mais", "mas", "na", "nas", "no", "nos",
    "o", "os", "ou", "para", "pela", "pelas", "pelo", "pelos", "por", "porque",
    "que", "se", "sem", "ser", "sua", "suas", "seu", "seus", "tambem", "tem",
    "uma", "umas", "um", "uns", "voce", "voces", "quando", "onde", "muito",
    "muita", "muitos", "muitas", "pode", "podem",
}


class _VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._hidden = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in {"script", "style", "noscript"}:
            self._hidden += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style", "noscript"} and self._hidden:
            self._hidden -= 1

    def handle_data(self, data: str) -> None:
        if not self._hidden:
            self.parts.append(data)


def visible_text(value: str) -> str:
    parser = _VisibleTextParser()
    try:
        parser.feed(value or "")
        parser.close()
        text = " ".join(parser.parts)
    except Exception:
        text = re.sub(r"<[^>]+>", " ", value or "")
    return html.unescape(text)


def normalize_text(value: str) -> str:
    text = visible_text(value)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch)).lower()
    text = re.sub(r"https?://\S+|www\.\S+", " URL ", text)
    text = re.sub(r"\b\d+(?:[.,]\d+)?\b", " NUM ", text)
    text = re.sub(r"[^a-z0-9_]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def content_tokens(value: str) -> list[str]:
    return [
        token
        for token in normalize_text(value).split()
        if len(token) >= 3 and token not in STOPWORDS and token not in {"url", "num"}
    ]


def shingles(tokens: list[str], size: int) -> set[tuple[str, ...]]:
    if len(tokens) < size:
        return set()
    return {tuple(tokens[i : i + size]) for i in range(len(tokens) - size + 1)}


def jaccard(a: set[Any], b: set[Any]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def containment(a: set[Any], b: set[Any]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / min(len(a), len(b))


def cosine_tokens(a: list[str], b: list[str]) -> float:
    if not a or not b:
        return 0.0
    ca, cb = Counter(a), Counter(b)
    dot = sum(ca[k] * cb.get(k, 0) for k in ca)
    da = math.sqrt(sum(v * v for v in ca.values()))
    db = math.sqrt(sum(v * v for v in cb.values()))
    return dot / (da * db) if da and db else 0.0


def title_token_jaccard(a: str, b: str) -> float:
    return jaccard(set(content_tokens(a)), set(content_tokens(b)))


@dataclass
class Similarity:
    exact_body: bool
    exact_title: bool
    sequence: float
    cosine: float
    shingle_jaccard: float
    shingle_containment: float
    title_jaccard: float


def similarity(
    a_title: str,
    a_body: str,
    b_title: str,
    b_body: str,
    shingle_size: int = 5,
) -> Similarity:
    na, nb = normalize_text(a_body), normalize_text(b_body)
    ta, tb = content_tokens(a_body), content_tokens(b_body)
    sa, sb = shingles(ta, shingle_size), shingles(tb, shingle_size)
    nt_a, nt_b = normalize_text(a_title), normalize_text(b_title)
    return Similarity(
        exact_body=bool(na and nb and na == nb),
        exact_title=bool(nt_a and nt_b and nt_a == nt_b),
        sequence=SequenceMatcher(None, na, nb, autojunk=False).ratio() if na and nb else 0.0,
        cosine=cosine_tokens(ta, tb),
        shingle_jaccard=jaccard(sa, sb),
        shingle_containment=containment(sa, sb),
        title_jaccard=title_token_jaccard(a_title, b_title),
    )


def is_collision(
    sim: Similarity,
    thresholds: dict[str, float],
    body_available: bool = True,
) -> tuple[bool, str]:
    if sim.exact_body:
        return True, "corpo_editorial_identico"
    if sim.exact_title:
        return True, "titulo_editorial_identico"
    if not body_available:
        return False, ""
    if sim.sequence >= thresholds["sequence_very_high"]:
        return True, "sequencia_muito_alta"
    if sim.shingle_jaccard >= thresholds["shingle_jaccard_high"]:
        return True, "shingles_muito_altos"
    if (
        sim.sequence >= thresholds["sequence"]
        and sim.shingle_containment >= thresholds["shingle_containment"]
    ):
        return True, "estrutura_e_trechos_muito_parecidos"
    if (
        sim.cosine >= thresholds["cosine"]
        and sim.shingle_jaccard >= thresholds["shingle_jaccard"]
    ):
        return True, "vocabulario_e_trechos_muito_parecidos"
    if (
        sim.title_jaccard >= thresholds["title_jaccard"]
        and sim.cosine >= thresholds["title_body_cosine"]
        and sim.shingle_containment >= thresholds["title_body_containment"]
    ):
        return True, "titulo_e_corpo_muito_parecidos"
    return False, ""


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _item_key(item: dict[str, Any]) -> str:
    sid = str(item.get("shopee_item_id") or "").strip()
    if sid:
        return f"shopee:{sid}"
    iid = str(item.get("id") or "").strip()
    return f"id:{iid}" if iid else ""


def _history_keys(project_dir: Path) -> tuple[set[str], list[dict[str, Any]]]:
    history = load_json(project_dir / "data/publication_history.json", {}) or {}
    keys: set[str] = set()
    titles: list[dict[str, Any]] = []
    for item in history.get("items") or []:
        key = _item_key(item)
        if key:
            keys.add(key)
        title = str(item.get("editorial_title") or item.get("title") or "").strip()
        if title:
            titles.append(
                {
                    "kind": "published_title",
                    "key": key,
                    "title": title,
                    "body": "",
                    "source": str(item.get("wordpress_url") or item.get("published_at") or ""),
                }
            )
    return keys, titles


def _queue_generated_keys(project_dir: Path) -> set[str]:
    queue = load_json(project_dir / "data/editorial_queue.json", {}) or {}
    out: set[str] = set()
    for item in queue.get("items") or []:
        if str(item.get("status") or "").upper() in {"GENERATED", "PUBLISHED"}:
            key = _item_key(item)
            if key:
                out.add(key)
    return out


def _reference_records(
    root: Path,
    project_name: str,
    project_cfg: dict[str, Any],
) -> list[dict[str, Any]]:
    project_dir = root / project_cfg["path"]
    published_keys, title_only = _history_keys(project_dir)
    active_keys = _queue_generated_keys(project_dir)
    allowed_keys = published_keys | active_keys
    records: list[dict[str, Any]] = []
    generated_dir = project_dir / project_cfg.get("generated_dir", "data/generated")
    if generated_dir.exists():
        for path in sorted(generated_dir.glob("*.json")):
            draft = load_json(path, {}) or {}
            key = _item_key(draft)
            draft_status = str(draft.get("status") or "").upper()
            if key not in allowed_keys and draft_status not in {"PUBLISHED"}:
                continue
            title = str(
                draft.get("editorial_title")
                or draft.get("title")
                or draft.get("seo_title")
                or ""
            ).strip()
            body = str(draft.get("editorial_html") or "").strip()
            if title or body:
                records.append(
                    {
                        "project": project_name,
                        "kind": "editorial",
                        "key": key or path.stem,
                        "title": title,
                        "body": body,
                        "source": str(path.relative_to(root)),
                    }
                )

    represented_titles = {
        normalize_text(record["title"])
        for record in records
        if record.get("title")
    }
    for record in title_only:
        if normalize_text(record["title"]) not in represented_titles:
            record["project"] = project_name
            records.append(record)
    return records


def _candidate_items(
    root: Path,
    project_cfg: dict[str, Any],
) -> tuple[Path, dict[str, Any], list[tuple[dict[str, Any], Path, dict[str, Any]]]]:
    project_dir = root / project_cfg["path"]
    queue_path = project_dir / "data/editorial_queue.json"
    queue = load_json(queue_path, {}) or {}
    generated_dir = project_dir / project_cfg.get("generated_dir", "data/generated")
    candidates: list[tuple[dict[str, Any], Path, dict[str, Any]]] = []
    for item in queue.get("items") or []:
        if str(item.get("status") or "").upper() != "GENERATED":
            continue
        path = generated_dir / f"{item.get('id')}.json"
        if not path.exists() and str(item.get("id") or "").isdigit():
            padded = generated_dir / f"{int(item['id']):03d}.json"
            if padded.exists():
                path = padded
        if not path.exists():
            raise FileNotFoundError(f"candidato GENERATED sem arquivo gerado: {path}")
        draft = load_json(path, {}) or {}
        candidates.append((item, path, draft))
    return queue_path, queue, candidates


def run_guard(
    root: Path,
    project: str,
    mutate: bool = True,
    config_path: Path | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    config_file = root / (config_path or DEFAULT_CONFIG)
    config = load_json(config_file)
    if not isinstance(config, dict):
        raise RuntimeError(f"configuração inválida/ausente: {config_file}")

    projects = config.get("projects") or {}
    if project not in projects:
        raise RuntimeError(f"projeto não configurado: {project}")

    thresholds = config.get("thresholds") or {}
    required_thresholds = {
        "sequence",
        "sequence_very_high",
        "cosine",
        "shingle_jaccard",
        "shingle_jaccard_high",
        "shingle_containment",
        "title_jaccard",
        "title_body_cosine",
        "title_body_containment",
    }
    missing = sorted(required_thresholds - set(thresholds))
    if missing:
        raise RuntimeError(f"thresholds ausentes: {', '.join(missing)}")

    min_words = int(config.get("min_editorial_words", 120))
    shingle_size = int(config.get("shingle_size", 5))

    references: list[dict[str, Any]] = []
    for other_name, other_cfg in projects.items():
        if other_name == project:
            continue
        references.extend(_reference_records(root, other_name, other_cfg))

    queue_path, queue, candidates = _candidate_items(root, projects[project])
    report: dict[str, Any] = {
        "version": 1,
        "project": project,
        "mode": "enforce" if mutate else "check_only",
        "reference_projects": [name for name in projects if name != project],
        "reference_records": len(references),
        "candidates_scanned": len(candidates),
        "blocked": 0,
        "passed": 0,
        "results": [],
    }

    changed = False
    for queue_item, _draft_path, draft in candidates:
        title = str(
            draft.get("editorial_title")
            or draft.get("title")
            or draft.get("seo_title")
            or ""
        ).strip()
        body = str(draft.get("editorial_html") or "").strip()
        words = content_tokens(body)
        if len(words) < min_words:
            raise RuntimeError(
                f"{project} candidato {queue_item.get('id')} possui editorial_html curto/ausente "
                f"({len(words)} tokens úteis); cross-blog guard recusou comparar"
            )

        best: tuple[float, dict[str, Any], Similarity, str] | None = None
        for reference in references:
            ref_body = str(reference.get("body") or "")
            sim = similarity(
                title,
                body,
                str(reference.get("title") or ""),
                ref_body,
                shingle_size,
            )
            collision, reason = is_collision(
                sim,
                thresholds,
                body_available=bool(ref_body),
            )
            score = (
                (2.0 if sim.exact_body else 0.0)
                + (1.0 if sim.exact_title else 0.0)
                + sim.sequence
                + sim.cosine
                + sim.shingle_jaccard
                + sim.shingle_containment
                + sim.title_jaccard
            )
            if collision and (best is None or score > best[0]):
                best = (score, reference, sim, reason)

        if best:
            _, reference, sim, reason = best
            report["blocked"] += 1
            report["results"].append(
                {
                    "id": queue_item.get("id"),
                    "status": "BLOCKED",
                    "reason": reason,
                    "match_project": reference["project"],
                    "match_key": reference.get("key"),
                    "match_source": reference.get("source"),
                    "metrics": asdict(sim),
                }
            )
            if mutate:
                queue_item["status"] = "BLOCKED"
                queue_item["last_error"] = (
                    f"cross_blog_guard: {reason}; colisão com {reference['project']} "
                    f"({reference.get('key') or reference.get('source')})"
                )
                queue_item["cross_blog_guard"] = {
                    "status": "BLOCKED",
                    "reason": reason,
                    "match_project": reference["project"],
                    "match_key": reference.get("key"),
                    "metrics": asdict(sim),
                }
                changed = True
        else:
            report["passed"] += 1
            report["results"].append(
                {"id": queue_item.get("id"), "status": "PASS"}
            )

    if mutate and changed:
        write_json(queue_path, queue)

    report_path = root / projects[project]["path"] / "data/cross_blog_guard_report.json"
    write_json(report_path, report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Bloqueia repetição editorial excessiva entre projetos."
    )
    parser.add_argument(
        "--project",
        choices=["casa_decoracao", "oficina_garagem", "radar_tech_br"],
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Executar em todos os projetos configurados.",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Não alterar status da fila.",
    )
    parser.add_argument(
        "--root",
        default=None,
        help="Raiz do repositório (padrão: detectada pelo script).",
    )
    args = parser.parse_args()
    if not args.project and not args.all:
        parser.error("use --project <nome> ou --all")

    root = (
        Path(args.root).resolve()
        if args.root
        else Path(__file__).resolve().parents[1]
    )
    cfg = load_json(root / DEFAULT_CONFIG, {}) or {}
    targets = list((cfg.get("projects") or {}).keys()) if args.all else [args.project]
    total_blocked = 0
    for project in targets:
        report = run_guard(root, str(project), mutate=not args.check_only)
        total_blocked += int(report["blocked"])
        print(
            f"[cross-blog-guard] {project}: candidatos={report['candidates_scanned']} "
            f"pass={report['passed']} blocked={report['blocked']} "
            f"refs={report['reference_records']}"
        )
    print(f"[cross-blog-guard] concluído; bloqueados={total_blocked}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
