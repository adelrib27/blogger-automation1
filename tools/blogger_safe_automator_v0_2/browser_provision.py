#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from playwright.sync_api import BrowserContext, Locator, Page, TimeoutError as PlaywrightTimeoutError, sync_playwright

BLOGGER_HOME = "https://www.blogger.com/"
CREATE_CONFIRMATION = "CREATE BLOG"
ADDRESS_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{1,61}[a-z0-9])?$")


class SafeAutomationError(RuntimeError):
    pass


@dataclass(frozen=True)
class CreateBlogRequest:
    title: str
    address: str

    @classmethod
    def build(cls, title: str, address: str) -> "CreateBlogRequest":
        clean_title = re.sub(r"\s+", " ", title or "").strip()
        if not clean_title or len(clean_title) > 100:
            raise SafeAutomationError("Título inválido: use entre 1 e 100 caracteres.")

        clean_address = normalize_address(address)
        if not ADDRESS_RE.fullmatch(clean_address):
            raise SafeAutomationError(
                "Endereço inválido: use apenas letras minúsculas, números e hífens, "
                "sem hífen no início/fim."
            )
        return cls(title=clean_title, address=clean_address)


def normalize_address(value: str) -> str:
    raw = (value or "").strip().lower()
    raw = re.sub(r"^https?://", "", raw)
    raw = raw.removesuffix("/")
    raw = re.sub(r"\.blogspot\.com(?:\.br)?$", "", raw)
    return raw.strip()


def visible_first(candidates: Iterable[Locator]) -> Locator | None:
    for candidate in candidates:
        try:
            if candidate.count() and candidate.first.is_visible():
                return candidate.first
        except Exception:
            continue
    return None


def require_blogger_session(page: Page) -> None:
    page.goto(BLOGGER_HOME, wait_until="domcontentloaded", timeout=60_000)
    page.wait_for_timeout(1800)
    current = page.url.lower()
    if "accounts.google.com" in current:
        raise SafeAutomationError(
            "Sessão do Playwright não está autenticada no Blogger. "
            "Faça login manualmente nessa sessão persistente e execute novamente."
        )
    if "blogger.com" not in current:
        raise SafeAutomationError(f"Navegação inesperada: {page.url}")


def dump_visible_controls(page: Page, out_path: Path | None = None) -> dict:
    data = page.evaluate(
        """() => {
          const nodes = [...document.querySelectorAll('button,a,input,[role="button"],[role="menuitem"]')];
          return nodes
            .filter(el => {
              const r = el.getBoundingClientRect();
              const s = getComputedStyle(el);
              return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none';
            })
            .slice(0, 250)
            .map(el => ({
              tag: el.tagName,
              text: (el.innerText || el.value || '').trim().replace(/\s+/g, ' ').slice(0, 180),
              aria: (el.getAttribute('aria-label') || '').trim().slice(0, 180),
              role: el.getAttribute('role') || '',
              href: el.getAttribute('href') || ''
            }));
        }"""
    )
    payload = {"url": page.url, "controls": data}
    if out_path:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def find_new_blog(page: Page) -> Locator | None:
    return visible_first(
        [
            page.get_by_role("button", name=re.compile(r"^(Novo blog|New blog)$", re.I)),
            page.get_by_role("menuitem", name=re.compile(r"^(Novo blog|New blog)$", re.I)),
            page.get_by_text(re.compile(r"^(Novo blog|New blog)$", re.I), exact=True),
        ]
    )


def open_blog_switcher(page: Page) -> None:
    switcher = visible_first(
        [
            page.get_by_role(
                "button",
                name=re.compile(
                    r"(Selecionar blog|Lista de blogs|Trocar blog|Choose a blog|Blog list|Switch blog)",
                    re.I,
                ),
            ),
            page.locator('button[aria-label*="blog" i], [role="button"][aria-label*="blog" i]'),
        ]
    )
    if switcher is None:
        raise SafeAutomationError(
            "Não foi possível identificar com segurança o seletor de blogs. "
            "Nenhum clique foi executado."
        )
    switcher.click(timeout=10_000)
    page.wait_for_timeout(700)


def click_new_blog(page: Page) -> None:
    control = find_new_blog(page)
    if control is None:
        open_blog_switcher(page)
        control = find_new_blog(page)
    if control is None:
        raise SafeAutomationError(
            'O comando "Novo blog" não ficou visível após abrir o seletor. '
            "Nenhuma criação foi iniciada."
        )
    control.click(timeout=10_000)


def dialog_or_page(page: Page) -> Locator:
    dialogs = page.get_by_role("dialog")
    try:
        if dialogs.count() and dialogs.last.is_visible():
            return dialogs.last
    except Exception:
        pass
    return page.locator("body")


def fill_named_textbox(scope: Locator, names: list[str], value: str) -> None:
    for name in names:
        candidate = scope.get_by_role("textbox", name=re.compile(name, re.I))
        try:
            if candidate.count() and candidate.first.is_visible():
                candidate.first.fill(value)
                return
        except Exception:
            pass

    visible = []
    boxes = scope.get_by_role("textbox")
    for i in range(boxes.count()):
        box = boxes.nth(i)
        try:
            if box.is_visible():
                visible.append(box)
        except Exception:
            continue
    if len(visible) == 1:
        visible[0].fill(value)
        return

    raise SafeAutomationError("Campo de texto esperado não foi identificado com segurança.")


def click_named_button(scope: Locator, pattern: str) -> None:
    button = scope.get_by_role("button", name=re.compile(pattern, re.I))
    if not button.count():
        raise SafeAutomationError(f"Botão esperado não encontrado: /{pattern}/")
    visible = None
    for i in range(button.count()):
        item = button.nth(i)
        try:
            if item.is_visible() and item.is_enabled():
                visible = item
                break
        except Exception:
            continue
    if visible is None:
        raise SafeAutomationError(f"Botão esperado não está visível/ativo: /{pattern}/")
    visible.click(timeout=10_000)


def create_blog(page: Page, req: CreateBlogRequest) -> dict:
    click_new_blog(page)
    page.wait_for_timeout(600)

    scope = dialog_or_page(page)
    fill_named_textbox(scope, [r"t[ií]tulo", r"nome.*blog", r"title"], req.title)
    click_named_button(scope, r"^(Pr[oó]xima|Next)$")
    page.wait_for_timeout(650)

    scope = dialog_or_page(page)
    fill_named_textbox(scope, [r"endere[cç]o", r"url", r"address"], req.address)

    page.wait_for_timeout(1200)
    click_named_button(scope, r"^(Salvar|Save)$")

    deadline = time.time() + 25
    while time.time() < deadline:
        page.wait_for_timeout(600)
        if req.title.lower() in page.locator("body").inner_text().lower():
            break

    return {
        "title": req.title,
        "address": req.address,
        "expected_url": f"https://{req.address}.blogspot.com/",
        "current_url": page.url,
    }


def run_audit(page: Page, diagnostics_dir: Path) -> None:
    require_blogger_session(page)
    diagnostics_dir.mkdir(parents=True, exist_ok=True)
    dump_visible_controls(page, diagnostics_dir / "visible_controls.json")
    page.screenshot(path=str(diagnostics_dir / "blogger_panel.png"), full_page=True)
    new_blog_visible = find_new_blog(page) is not None
    print(json.dumps(
        {
            "status": "AUDIT_OK",
            "url": page.url,
            "new_blog_visible": new_blog_visible,
            "diagnostics_dir": str(diagnostics_dir),
        },
        ensure_ascii=False,
        indent=2,
    ))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Blogger Safe Automator v0.2 — provisionamento via Playwright."
    )
    parser.add_argument(
        "--profile-dir",
        default=".blogger-playwright-profile",
        help="Diretório persistente da sessão do Chromium.",
    )
    parser.add_argument(
        "--diagnostics-dir",
        default="logs/browser_diagnostics",
        help="Diretório para screenshot e controles visíveis.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("audit", help="Somente leitura: abre o Blogger e registra diagnóstico.")

    create = sub.add_parser("create-blog", help="Cria um blog somente com confirmação explícita.")
    create.add_argument("--title", required=True)
    create.add_argument("--address", required=True)
    create.add_argument(
        "--apply",
        action="store_true",
        help="Permite clicar no fluxo de criação. Sem isso, executa apenas pré-validação.",
    )
    create.add_argument(
        "--confirm",
        default="",
        help=f'Confirmação obrigatória quando --apply for usado: "{CREATE_CONFIRMATION}".',
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    profile_dir = Path(args.profile_dir).expanduser().resolve()
    diagnostics_dir = Path(args.diagnostics_dir).expanduser().resolve()

    with sync_playwright() as p:
        context: BrowserContext = p.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir),
            headless=False,
            viewport={"width": 1440, "height": 1000},
        )
        page = context.pages[0] if context.pages else context.new_page()

        try:
            if args.command == "audit":
                run_audit(page, diagnostics_dir)
                return 0

            req = CreateBlogRequest.build(args.title, args.address)
            require_blogger_session(page)

            if not args.apply:
                dump_visible_controls(page, diagnostics_dir / "preflight_controls.json")
                print(json.dumps(
                    {
                        "status": "PREFLIGHT_OK_NO_CHANGES",
                        "title": req.title,
                        "address": req.address,
                        "expected_url": f"https://{req.address}.blogspot.com/",
                        "message": "Nenhum clique de criação foi executado. Use --apply e confirmação explícita.",
                    },
                    ensure_ascii=False,
                    indent=2,
                ))
                return 0

            if args.confirm != CREATE_CONFIRMATION:
                raise SafeAutomationError(
                    f'Criação bloqueada: use --confirm "{CREATE_CONFIRMATION}".'
                )

            result = create_blog(page, req)
            diagnostics_dir.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(diagnostics_dir / "after_create_blog.png"), full_page=True)
            print(json.dumps({"status": "CREATE_BLOG_COMPLETED", **result}, ensure_ascii=False, indent=2))
            return 0

        except (SafeAutomationError, PlaywrightTimeoutError) as exc:
            diagnostics_dir.mkdir(parents=True, exist_ok=True)
            try:
                dump_visible_controls(page, diagnostics_dir / "failure_controls.json")
                page.screenshot(path=str(diagnostics_dir / "failure.png"), full_page=True)
            except Exception:
                pass
            print(f"ERRO_SEGURO: {exc}", file=sys.stderr)
            return 2
        finally:
            context.close()


if __name__ == "__main__":
    raise SystemExit(main())
