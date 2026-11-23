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
from urllib.parse import urlparse, urlunparse
from urllib.request import urlopen

from playwright.sync_api import (
    Browser,
    BrowserContext,
    Locator,
    Page,
    TimeoutError as PlaywrightTimeoutError,
    sync_playwright,
)

BLOGGER_HOME = "https://www.blogger.com/"
CREATE_CONFIRMATION = "CREATE BLOG"
DEFAULT_CDP_URL = "http://127.0.0.1:9222"
ADDRESS_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{1,61}[a-z0-9])?$")
BLOG_ID_PATTERNS = (
    re.compile(r"/blog/(?:posts|pages|settings|theme|layout)/(\d+)(?:[/?#]|$)", re.I),
    re.compile(r"[?&]blogID=(\d+)(?:&|$)", re.I),
)
LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}

NEW_BLOG_RE = re.compile(r"^(Novo blog(?:\.\.\.|…)?|New blog(?:\.\.\.|…)?)$", re.I)
BLOG_SELECTION_RE = re.compile(r"^(Blog Selection|Sele[cç][aã]o de blog)$", re.I)
ADVANCE_LABELS = ("AVANÇAR", "Advance", "Próxima", "Next", "Continuar", "Continue")
FINAL_LABELS = ("SALVAR", "Save", "Criar blog", "Create blog", "Concluir", "Finish")
TITLE_FIELD_SELECTORS = (
    'input[aria-label="Título"]',
    'input[aria-label="Title"]',
)
ADDRESS_FIELD_SELECTORS = (
    'input[aria-label="Endereço"]',
    'input[aria-label="Address"]',
    'input[aria-label="URL"]',
)
ADDRESS_UNAVAILABLE_MARKERS = (
    "este endereço de blog não está disponível",
    "esse endereço de blog não está disponível",
    "este endereço de blog é inválido",
    "endereço de blog inválido",
    "this blog address is not available",
    "sorry, this blog address is not available",
    "this blog address is invalid",
)
ADDRESS_AVAILABLE_MARKERS = (
    "este endereço de blog está disponível",
    "this blog address is available",
)


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


def sanitize_url(value: str) -> str:
    try:
        parsed = urlparse(value)
        return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))
    except Exception:
        return value.split("?", 1)[0].split("#", 1)[0]


def _norm(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def validate_cdp_url(cdp_url: str, *, allow_remote: bool = False) -> str:
    parsed = urlparse((cdp_url or "").strip())
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise SafeAutomationError("CDP URL inválida. Use http(s)://host:porta.")
    if parsed.username or parsed.password:
        raise SafeAutomationError("CDP URL não deve conter credenciais.")
    if parsed.query or parsed.fragment:
        raise SafeAutomationError("CDP URL não deve conter query string ou fragmento.")
    if parsed.path not in {"", "/"}:
        raise SafeAutomationError("CDP URL deve apontar para a origem, sem caminho adicional.")
    if not allow_remote and parsed.hostname.lower() not in LOOPBACK_HOSTS:
        raise SafeAutomationError(
            "CDP remoto bloqueado por segurança. Use loopback (127.0.0.1/localhost) "
            "ou habilite --allow-remote-cdp explicitamente."
        )
    return f"{parsed.scheme}://{parsed.netloc}"


def probe_cdp(cdp_url: str, *, timeout_seconds: float = 3.0) -> dict:
    endpoint = cdp_url.rstrip("/") + "/json/version"
    try:
        with urlopen(endpoint, timeout=timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        raise SafeAutomationError(
            f"Chrome CDP indisponível em {cdp_url}. Inicie o Chrome oficial com remote debugging."
        ) from exc

    browser_name = str(payload.get("Browser") or "")
    protocol = str(payload.get("Protocol-Version") or "")
    if not browser_name or not protocol:
        raise SafeAutomationError("Endpoint CDP respondeu, mas /json/version está incompleto.")

    return {
        "cdp_url": cdp_url,
        "browser": browser_name,
        "protocol_version": protocol,
    }


def connect_official_chrome(playwright, cdp_url: str) -> tuple[Browser, BrowserContext]:
    browser = playwright.chromium.connect_over_cdp(cdp_url, timeout=10_000)
    if not browser.contexts:
        raise SafeAutomationError("Chrome conectado via CDP, mas nenhum contexto foi encontrado.")
    return browser, browser.contexts[0]


def select_page(context: BrowserContext) -> Page:
    for page in context.pages:
        try:
            if "blogger.com" in (urlparse(page.url).hostname or "").lower():
                return page
        except Exception:
            pass
    return context.pages[0] if context.pages else context.new_page()


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
    host = (urlparse(page.url).hostname or "").lower()
    if host == "accounts.google.com" or host.endswith(".accounts.google.com"):
        raise SafeAutomationError(
            "Chrome oficial está sem sessão autenticada no Blogger. "
            "Faça login manualmente nesse perfil do Chrome e execute novamente."
        )
    if host != "blogger.com" and not host.endswith(".blogger.com"):
        raise SafeAutomationError(f"Navegação inesperada: {sanitize_url(page.url)}")


def dump_visible_controls(page: Page, out_path: Path | None = None) -> dict:
    data = page.evaluate(
        r"""() => {
          const nodes = [...document.querySelectorAll(
            'button,a,input,[role="button"],[role="menuitem"],[role="listbox"],[role="option"]'
          )];
          const safeHref = (raw) => {
            if (!raw) return '';
            try {
              const u = new URL(raw, location.href);
              return `${u.origin}${u.pathname}`;
            } catch (_) {
              return '';
            }
          };
          return nodes
            .filter(el => {
              const r = el.getBoundingClientRect();
              const s = getComputedStyle(el);
              return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none';
            })
            .slice(0, 350)
            .map(el => ({
              tag: el.tagName,
              text: (el.innerText || el.value || '').trim().replace(/\s+/g, ' ').slice(0, 180),
              aria: (el.getAttribute('aria-label') || '').trim().slice(0, 180),
              role: el.getAttribute('role') || '',
              href: safeHref(el.getAttribute('href') || '')
            }));
        }"""
    )
    payload = {"url": sanitize_url(page.url), "controls": data}
    if out_path:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def _ensure_main_drawer(page: Page) -> None:
    listbox = visible_first([page.get_by_role("listbox", name=BLOG_SELECTION_RE)])
    if listbox is not None:
        return

    menu = visible_first(
        [
            page.locator('[role="button"][aria-label="Menu principal"]'),
            page.locator('[role="button"][aria-label="Main menu"]'),
        ]
    )
    if menu is not None:
        try:
            menu.click(timeout=3_000)
        except Exception:
            menu.evaluate("el => el.click()")
        page.wait_for_timeout(500)


def open_blog_switcher(page: Page) -> None:
    _ensure_main_drawer(page)
    listbox = visible_first([page.get_by_role("listbox", name=BLOG_SELECTION_RE)])
    if listbox is None:
        raise SafeAutomationError(
            "Não foi possível identificar com segurança o seletor de blogs. "
            "Nenhum clique de criação foi executado."
        )

    try:
        listbox.click(timeout=3_000)
    except Exception:
        try:
            listbox.evaluate("el => el.click()")
        except Exception as exc:
            raise SafeAutomationError(
                "O seletor de blogs foi localizado, mas não pôde ser aberto com segurança."
            ) from exc
    page.wait_for_timeout(500)


def find_new_blog(page: Page) -> Locator | None:
    options = page.get_by_role("option")
    for i in range(options.count()):
        item = options.nth(i)
        try:
            if item.is_visible() and NEW_BLOG_RE.fullmatch(_norm(item.inner_text())):
                return item
        except Exception:
            continue
    return None


def ensure_new_blog_available(page: Page) -> bool:
    try:
        open_blog_switcher(page)
        control = find_new_blog(page)
        return control is not None
    finally:
        try:
            page.keyboard.press("Escape")
        except Exception:
            pass


def _visible_field(page: Page, selectors: tuple[str, ...]) -> Locator | None:
    for selector in selectors:
        loc = page.locator(selector)
        for i in range(loc.count()):
            item = loc.nth(i)
            try:
                if item.is_visible():
                    return item
            except Exception:
                continue
    return None


def _dom_action_state(page: Page, labels: tuple[str, ...]) -> list[dict]:
    return page.evaluate(
        r"""(labels) => {
          const wanted = new Set(labels.map(x => String(x).trim().replace(/\s+/g, ' ').toLocaleLowerCase()));
          const out = [];
          for (const el of document.querySelectorAll('body *')) {
            const r = el.getBoundingClientRect();
            const s = getComputedStyle(el);
            if (r.width <= 0 || r.height <= 0 || s.display === 'none' || s.visibility === 'hidden') continue;
            const text = (el.innerText || el.textContent || '').trim().replace(/\s+/g, ' ');
            const aria = (el.getAttribute('aria-label') || '').trim().replace(/\s+/g, ' ');
            const value = text || aria;
            if (!wanted.has(value.toLocaleLowerCase())) continue;
            const role = el.getAttribute('role') || '';
            const clickable = el.tagName === 'BUTTON' || role === 'button' || el.getAttribute('tabindex') === '0';
            const disabled = el.hasAttribute('disabled') || el.getAttribute('aria-disabled') === 'true' || el.getAttribute('tabindex') === '-1';
            const cx = Math.max(0, Math.min(innerWidth - 1, r.left + r.width / 2));
            const cy = Math.max(0, Math.min(innerHeight - 1, r.top + r.height / 2));
            const hit = document.elementFromPoint(cx, cy);
            const topmost = !!hit && (hit === el || el.contains(hit) || hit.contains(el));
            out.push({
              tag: el.tagName,
              role,
              text: text.slice(0, 160),
              aria: aria.slice(0, 160),
              tabindex: el.getAttribute('tabindex') || '',
              clickable,
              disabled,
              topmost,
              width: Math.round(r.width),
              height: Math.round(r.height)
            });
          }
          return out;
        }""",
        list(labels),
    )


def _click_exact_action(page: Page, labels: tuple[str, ...]) -> dict:
    result = page.evaluate(
        r"""(labels) => {
          const wanted = new Set(labels.map(x => String(x).trim().replace(/\s+/g, ' ').toLocaleLowerCase()));
          const candidates = [];
          for (const el of document.querySelectorAll('body *')) {
            const r = el.getBoundingClientRect();
            const s = getComputedStyle(el);
            if (r.width <= 0 || r.height <= 0 || s.display === 'none' || s.visibility === 'hidden') continue;
            const text = (el.innerText || el.textContent || '').trim().replace(/\s+/g, ' ');
            const aria = (el.getAttribute('aria-label') || '').trim().replace(/\s+/g, ' ');
            const value = text || aria;
            if (!wanted.has(value.toLocaleLowerCase())) continue;
            const role = el.getAttribute('role') || '';
            const clickable = el.tagName === 'BUTTON' || role === 'button' || el.getAttribute('tabindex') === '0';
            if (!clickable) continue;
            if (el.hasAttribute('disabled') || el.getAttribute('aria-disabled') === 'true' || el.getAttribute('tabindex') === '-1') continue;
            const cx = Math.max(0, Math.min(innerWidth - 1, r.left + r.width / 2));
            const cy = Math.max(0, Math.min(innerHeight - 1, r.top + r.height / 2));
            const hit = document.elementFromPoint(cx, cy);
            if (!hit || !(hit === el || el.contains(hit) || hit.contains(el))) continue;
            candidates.push({el, r, text, aria, role});
          }
          if (!candidates.length) return {ok: false};
          candidates.sort((a, b) => (a.r.width * a.r.height) - (b.r.width * b.r.height));
          const c = candidates[0];
          c.el.click();
          return {
            ok: true,
            meta: {
              tag: c.el.tagName,
              role: c.role,
              text: c.text.slice(0, 160),
              aria: c.aria.slice(0, 160),
              tabindex: c.el.getAttribute('tabindex') || ''
            }
          };
        }""",
        list(labels),
    )
    if not result or not result.get("ok"):
        raise SafeAutomationError(
            f"Nenhuma ação visível, habilitada e no topo foi encontrada para: {', '.join(labels)}"
        )
    return result["meta"]


def click_new_blog(page: Page) -> None:
    open_blog_switcher(page)
    control = find_new_blog(page)
    if control is None:
        raise SafeAutomationError(
            'O comando "Novo blog..." não ficou visível após abrir o seletor. '
            "Nenhuma criação foi iniciada."
        )

    try:
        control.evaluate("el => el.click()")
    except Exception as exc:
        raise SafeAutomationError(
            'A opção "Novo blog..." foi localizada, mas não pôde ser ativada com segurança.'
        ) from exc

    page.wait_for_timeout(900)
    if _visible_field(page, TITLE_FIELD_SELECTORS) is None:
        raise SafeAutomationError(
            'A ação "Novo blog..." foi disparada, mas o campo de título não apareceu. '
            "Nenhum dado foi preenchido."
        )


def _body_text_lower(page: Page) -> str:
    try:
        return _norm(page.locator("body").inner_text()).casefold()
    except Exception:
        return ""


def _wait_for_address_ready(page: Page, address_field: Locator, timeout_seconds: int = 15) -> dict:
    deadline = time.time() + timeout_seconds
    last_state: dict = {}

    while time.time() < deadline:
        body = _body_text_lower(page)
        aria_invalid = (address_field.get_attribute("aria-invalid") or "").lower()
        actions = _dom_action_state(page, FINAL_LABELS)
        save_enabled = any(
            item.get("clickable") and not item.get("disabled") and item.get("topmost")
            for item in actions
        )
        unavailable = any(marker in body for marker in ADDRESS_UNAVAILABLE_MARKERS)
        available = any(marker in body for marker in ADDRESS_AVAILABLE_MARKERS)

        last_state = {
            "aria_invalid": aria_invalid,
            "save_enabled": save_enabled,
            "address_available_marker": available,
            "address_unavailable_or_invalid": unavailable,
            "final_action_matches": actions[:12],
        }

        if unavailable:
            raise SafeAutomationError(
                "O endereço solicitado foi rejeitado pelo Blogger. Nenhum clique em SALVAR foi executado."
            )
        if save_enabled and aria_invalid != "true":
            return last_state

        page.wait_for_timeout(350)

    raise SafeAutomationError(
        "O Blogger não confirmou o endereço como utilizável dentro do tempo esperado. "
        "Nenhum clique em SALVAR foi executado."
    )


def extract_blog_id_from_url(value: str) -> str | None:
    for pattern in BLOG_ID_PATTERNS:
        match = pattern.search(value or "")
        if match:
            return match.group(1)
    return None


def extract_current_blog_id(page: Page) -> str | None:
    return extract_blog_id_from_url(page.url)


def extract_blog_id_from_title_link(page: Page, title: str) -> str | None:
    try:
        links = page.locator("a[href]").evaluate_all(
            r"""els => els.slice(0, 500).map(a => ({
                href: a.href || '',
                text: (a.innerText || a.textContent || '').trim().replace(/\s+/g, ' ')
            }))"""
        )
    except Exception:
        return None

    target = re.sub(r"\s+", " ", title).strip().casefold()
    for item in links:
        text = re.sub(r"\s+", " ", str(item.get("text") or "")).strip().casefold()
        if text != target:
            continue
        blog_id = extract_blog_id_from_url(str(item.get("href") or ""))
        if blog_id:
            return blog_id
    return None


def wait_for_created_blog(
    page: Page,
    req: CreateBlogRequest,
    previous_blog_id: str | None,
    timeout_seconds: int = 35,
) -> str:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        page.wait_for_timeout(600)

        current_blog_id = extract_current_blog_id(page)
        if current_blog_id and current_blog_id != previous_blog_id:
            return current_blog_id

        linked_blog_id = extract_blog_id_from_title_link(page, req.title)
        if linked_blog_id and linked_blog_id != previous_blog_id:
            return linked_blog_id

    raise SafeAutomationError(
        "A ação de salvar foi executada, mas um novo Blog ID diferente do blog anterior "
        "não pôde ser confirmado. Sucesso NÃO será registrado."
    )


def validate_public_blog(
    context: BrowserContext,
    expected_url: str,
    *,
    timeout_seconds: int = 30,
) -> dict:
    deadline = time.time() + timeout_seconds
    last_status = None
    last_url = expected_url
    while time.time() < deadline:
        try:
            response = context.request.get(
                expected_url,
                timeout=10_000,
                fail_on_status_code=False,
            )
            last_status = response.status
            last_url = response.url
            if response.status == 200:
                return {
                    "ok": True,
                    "status": response.status,
                    "url": sanitize_url(response.url),
                }
        except Exception:
            pass
        time.sleep(1.0)

    return {
        "ok": False,
        "status": last_status,
        "url": sanitize_url(last_url),
    }


def create_blog(page: Page, context: BrowserContext, req: CreateBlogRequest) -> dict:
    previous_blog_id = extract_current_blog_id(page)
    click_new_blog(page)

    title = _visible_field(page, TITLE_FIELD_SELECTORS)
    if title is None:
        raise SafeAutomationError("Campo de título não foi localizado com segurança.")
    title.fill(req.title)
    page.wait_for_timeout(350)

    advance_action = _click_exact_action(page, ADVANCE_LABELS)
    page.wait_for_timeout(900)

    address = _visible_field(page, ADDRESS_FIELD_SELECTORS)
    if address is None:
        raise SafeAutomationError(
            "Campo de endereço não foi localizado após AVANÇAR. Nenhum clique em SALVAR foi executado."
        )
    address.fill(req.address)

    validation = _wait_for_address_ready(page, address)
    save_action = _click_exact_action(page, FINAL_LABELS)
    blog_id = wait_for_created_blog(page, req, previous_blog_id)

    expected_url = f"https://{req.address}.blogspot.com/"
    public_validation = validate_public_blog(context, expected_url)
    if not public_validation["ok"]:
        raise SafeAutomationError(
            "O Blogger aparenta ter criado o blog, mas a URL pública não foi validada com HTTP 200. "
            f"Blog ID detectado: {blog_id}. Sucesso NÃO será registrado."
        )

    return {
        "title": req.title,
        "address": req.address,
        "blog_id": blog_id,
        "expected_url": expected_url,
        "panel_url": sanitize_url(page.url),
        "advance_action": advance_action,
        "address_validation": validation,
        "save_action": save_action,
        "public_validation": public_validation,
    }


def execute_audit(
    *,
    cdp_url: str = DEFAULT_CDP_URL,
    diagnostics_dir: Path | str = Path("logs/browser_diagnostics"),
    allow_remote_cdp: bool = False,
) -> dict:
    diagnostics_dir = Path(diagnostics_dir).expanduser().resolve()
    safe_cdp = validate_cdp_url(cdp_url, allow_remote=allow_remote_cdp)
    cdp_info = probe_cdp(safe_cdp)

    with sync_playwright() as p:
        browser, context = connect_official_chrome(p, safe_cdp)
        page = select_page(context)
        require_blogger_session(page)
        diagnostics_dir.mkdir(parents=True, exist_ok=True)
        dump_visible_controls(page, diagnostics_dir / "visible_controls.json")
        page.screenshot(path=str(diagnostics_dir / "blogger_panel.png"), full_page=True)
        new_blog_visible = ensure_new_blog_available(page)
        return {
            "status": "AUDIT_OK",
            "url": sanitize_url(page.url),
            "new_blog_available": new_blog_visible,
            "diagnostics_dir": str(diagnostics_dir),
            "cdp": cdp_info,
            "browser_connected": browser.is_connected(),
        }


def execute_preflight(
    title: str,
    address: str,
    *,
    cdp_url: str = DEFAULT_CDP_URL,
    diagnostics_dir: Path | str = Path("logs/browser_diagnostics"),
    allow_remote_cdp: bool = False,
) -> dict:
    req = CreateBlogRequest.build(title, address)
    diagnostics_dir = Path(diagnostics_dir).expanduser().resolve()
    safe_cdp = validate_cdp_url(cdp_url, allow_remote=allow_remote_cdp)
    probe_cdp(safe_cdp)

    with sync_playwright() as p:
        _, context = connect_official_chrome(p, safe_cdp)
        page = select_page(context)
        require_blogger_session(page)
        if not ensure_new_blog_available(page):
            raise SafeAutomationError(
                'O comando "Novo blog..." não foi encontrado no preflight. Nenhuma criação foi iniciada.'
            )
        diagnostics_dir.mkdir(parents=True, exist_ok=True)
        dump_visible_controls(page, diagnostics_dir / "preflight_controls.json")
        return {
            "status": "PREFLIGHT_OK_NO_CHANGES",
            "title": req.title,
            "address": req.address,
            "expected_url": f"https://{req.address}.blogspot.com/",
            "message": "Nenhuma criação foi iniciada.",
        }


def execute_create(
    title: str,
    address: str,
    *,
    confirm: str,
    cdp_url: str = DEFAULT_CDP_URL,
    diagnostics_dir: Path | str = Path("logs/browser_diagnostics"),
    allow_remote_cdp: bool = False,
) -> dict:
    if confirm != CREATE_CONFIRMATION:
        raise SafeAutomationError(
            f'Criação bloqueada: confirmação obrigatória é "{CREATE_CONFIRMATION}".'
        )

    req = CreateBlogRequest.build(title, address)
    diagnostics_dir = Path(diagnostics_dir).expanduser().resolve()
    safe_cdp = validate_cdp_url(cdp_url, allow_remote=allow_remote_cdp)
    probe_cdp(safe_cdp)

    with sync_playwright() as p:
        _, context = connect_official_chrome(p, safe_cdp)
        page = select_page(context)
        try:
            require_blogger_session(page)
            result = create_blog(page, context, req)
            diagnostics_dir.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(diagnostics_dir / "after_create_blog.png"), full_page=True)
            return {"status": "CREATE_BLOG_VALIDATED", **result}
        except Exception:
            diagnostics_dir.mkdir(parents=True, exist_ok=True)
            try:
                dump_visible_controls(page, diagnostics_dir / "failure_controls.json")
                page.screenshot(path=str(diagnostics_dir / "failure.png"), full_page=True)
            except Exception:
                pass
            raise


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Blogger Safe Automator v0.3 — Chrome oficial via CDP."
    )
    parser.add_argument(
        "--cdp-url",
        default=DEFAULT_CDP_URL,
        help=f"Endpoint CDP do Chrome oficial (padrão: {DEFAULT_CDP_URL}).",
    )
    parser.add_argument(
        "--allow-remote-cdp",
        action="store_true",
        help="Permite CDP fora do loopback. Evite; use apenas em rede privada controlada.",
    )
    parser.add_argument(
        "--diagnostics-dir",
        default="logs/browser_diagnostics",
        help="Diretório para screenshots e controles visíveis sanitizados.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("audit", help="Somente leitura: valida CDP, sessão e controles do Blogger.")

    create = sub.add_parser("create-blog", help="Preflight por padrão; cria somente com --apply.")
    create.add_argument("--title", required=True)
    create.add_argument("--address", required=True)
    create.add_argument(
        "--apply",
        action="store_true",
        help="Executa o fluxo de criação. Sem isso, apenas preflight.",
    )
    create.add_argument(
        "--confirm",
        default="",
        help=f'Confirmação obrigatória com --apply: "{CREATE_CONFIRMATION}".',
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()

    try:
        if args.command == "audit":
            result = execute_audit(
                cdp_url=args.cdp_url,
                diagnostics_dir=args.diagnostics_dir,
                allow_remote_cdp=args.allow_remote_cdp,
            )
        elif not args.apply:
            result = execute_preflight(
                args.title,
                args.address,
                cdp_url=args.cdp_url,
                diagnostics_dir=args.diagnostics_dir,
                allow_remote_cdp=args.allow_remote_cdp,
            )
        else:
            result = execute_create(
                args.title,
                args.address,
                confirm=args.confirm,
                cdp_url=args.cdp_url,
                diagnostics_dir=args.diagnostics_dir,
                allow_remote_cdp=args.allow_remote_cdp,
            )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (SafeAutomationError, PlaywrightTimeoutError) as exc:
        print(f"ERRO_SEGURO: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
