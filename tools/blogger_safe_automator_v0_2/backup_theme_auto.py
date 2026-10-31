#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shutil
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import browser_provision as bp
from auto_blog_route import ensure_theme_page
from blogger_panel_route_guard import extract_panel_blog_id
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError, sync_playwright

BACKUP_LABEL_RE = re.compile(r"^(Fazer backup|Backup|Back up)$", re.I)
DOWNLOAD_LABEL_RE = re.compile(r"(download|baixar|fazer\s+o?\s*download)", re.I)
BLOGGER_THEME_MARKERS = ("<b:skin", "<b:section", "<b:widget", "<b:template-skin")
CONTROLLED_DOWNLOAD_DIR = Path(r"C:\Blogger-Automator\downloads")


def _first_visible(locator):
    try:
        count = min(locator.count(), 40)
    except Exception:
        return None
    for i in range(count):
        item = locator.nth(i)
        try:
            if item.is_visible():
                return item
        except Exception:
            continue
    return None


def _open_actions(page) -> None:
    if _first_visible(page.get_by_role("menuitem", name=BACKUP_LABEL_RE)) is not None:
        return
    if _first_visible(page.get_by_text(BACKUP_LABEL_RE, exact=True)) is not None:
        return
    more = _first_visible(page.locator('[role="button"][aria-label="Mais ações"]'))
    if more is None:
        more = _first_visible(page.locator('[role="button"][aria-label="More actions"]'))
    if more is None:
        raise bp.SafeAutomationError("Controle 'Mais ações' do tema não foi localizado com segurança.")
    try:
        more.click(timeout=5_000)
    except Exception:
        more.evaluate("el => el.click()")
    page.wait_for_timeout(350)


def _backup_item(page):
    item = _first_visible(page.get_by_role("menuitem", name=BACKUP_LABEL_RE))
    if item is not None:
        return item
    item = _first_visible(page.get_by_text(BACKUP_LABEL_RE, exact=True))
    if item is not None:
        return item
    raise bp.SafeAutomationError("Opção 'Fazer backup' não foi localizada no menu Tema.")


def _looks_like_download_control(item) -> bool:
    values = []
    for kind in ("text", "aria", "title"):
        try:
            if kind == "text":
                value = item.inner_text(timeout=500) or ""
            elif kind == "aria":
                value = item.get_attribute("aria-label") or ""
            else:
                value = item.get_attribute("title") or ""
            if value.strip():
                values.append(value.strip())
        except Exception:
            pass
    return bool(DOWNLOAD_LABEL_RE.search(" ".join(values)))


def _download_button(page):
    scopes = []
    try:
        dialogs = page.locator('[role="dialog"]')
        for i in range(min(dialogs.count(), 10)):
            dialog = dialogs.nth(i)
            if dialog.is_visible():
                scopes.append(dialog)
    except Exception:
        pass
    scopes.append(page)
    for scope in scopes:
        try:
            controls = scope.locator('button,[role="button"],a[href]')
            count = min(controls.count(), 80)
        except Exception:
            continue
        for i in range(count):
            item = controls.nth(i)
            try:
                if item.is_visible() and _looks_like_download_control(item):
                    return item
            except Exception:
                continue
    return None


def _wait_download_button(page, timeout_ms: int = 20_000):
    deadline = time.time() + max(1, timeout_ms) / 1000.0
    while time.time() < deadline:
        item = _download_button(page)
        if item is not None:
            return item
        page.wait_for_timeout(350)
    return None


def _visible_backup_diagnostics(page) -> str:
    parts: list[str] = []
    try:
        dialogs = page.locator('[role="dialog"]')
        for i in range(min(dialogs.count(), 5)):
            d = dialogs.nth(i)
            if not d.is_visible():
                continue
            text = re.sub(r"\s+", " ", d.inner_text(timeout=1000) or "").strip()
            if text:
                parts.append("dialog=" + text[:700])
    except Exception:
        pass
    labels: list[str] = []
    try:
        controls = page.locator('button,[role="button"],a[href]')
        for i in range(min(controls.count(), 120)):
            item = controls.nth(i)
            try:
                if not item.is_visible():
                    continue
                text = re.sub(r"\s+", " ", item.inner_text(timeout=300) or "").strip()
                aria = (item.get_attribute("aria-label") or "").strip()
                label = text or aria
                if label and label not in labels:
                    labels.append(label[:120])
            except Exception:
                continue
    except Exception:
        pass
    if labels:
        parts.append("controls=" + " | ".join(labels[:25]))
    return "; ".join(parts)[:1800]


def _validate_blogger_theme_bytes(data: bytes) -> dict:
    if len(data) < 1024:
        raise bp.SafeAutomationError("Backup do tema foi baixado vazio ou pequeno demais.")
    text = data.decode("utf-8-sig", errors="replace")
    low = text.lower()
    if "<html" not in low:
        raise bp.SafeAutomationError("Backup baixado não contém a raiz HTML de um tema Blogger.")
    markers = [marker for marker in BLOGGER_THEME_MARKERS if marker in text]
    if len(markers) < 2:
        raise bp.SafeAutomationError("Backup baixado não contém marcadores estruturais suficientes de um tema Blogger.")
    if "blogger.com" not in low and "data:blog" not in low and "expr:" not in low:
        raise bp.SafeAutomationError("Backup baixado não apresenta assinatura estrutural do Blogger.")
    strict_xml = True
    strict_xml_error = ""
    try:
        ET.fromstring(text)
    except Exception as exc:
        strict_xml = False
        strict_xml_error = str(exc)[:400]
    return {
        "blogger_theme_structure_valid": True,
        "strict_xml_well_formed": strict_xml,
        "strict_xml_note": strict_xml_error,
        "matched_markers": markers,
    }


def _write_validated_bytes(data: bytes, output: Path, capture_mode: str, **extra) -> dict:
    validation = _validate_blogger_theme_bytes(data)
    output.parent.mkdir(parents=True, exist_ok=True)
    tmp = output.with_suffix(output.suffix + ".capturing.tmp")
    tmp.write_bytes(data)
    _validate_blogger_theme_bytes(tmp.read_bytes())
    tmp.replace(output)
    validation.update({"capture_mode": capture_mode, **extra})
    return validation


def _save_download(download, output: Path) -> dict:
    output.parent.mkdir(parents=True, exist_ok=True)
    tmp = output.with_suffix(output.suffix + ".downloading")
    download.save_as(str(tmp))
    if not tmp.exists():
        raise bp.SafeAutomationError("Backup do tema não foi materializado no disco.")
    data = tmp.read_bytes()
    validation = _validate_blogger_theme_bytes(data)
    tmp.replace(output)
    validation["capture_mode"] = "playwright-download-event"
    return validation


def _download_roots() -> list[Path]:
    roots = [Path.home() / "Downloads", CONTROLLED_DOWNLOAD_DIR]
    out = []
    for root in roots:
        try:
            if root.exists() and root not in out:
                out.append(root)
        except Exception:
            pass
    return out


def _configure_cdp_downloads(context, page) -> str:
    CONTROLLED_DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    session = context.new_cdp_session(page)
    params = {
        "behavior": "allow",
        "downloadPath": str(CONTROLLED_DOWNLOAD_DIR),
        "eventsEnabled": True,
    }
    try:
        session.send("Browser.setDownloadBehavior", params)
        return "Browser.setDownloadBehavior"
    except Exception:
        try:
            session.send("Page.setDownloadBehavior", {
                "behavior": "allow",
                "downloadPath": str(CONTROLLED_DOWNLOAD_DIR),
            })
            return "Page.setDownloadBehavior"
        except Exception as exc:
            raise bp.SafeAutomationError(
                "Não foi possível configurar uma pasta controlada para o backup do tema via CDP."
            ) from exc


def _snapshot_downloads() -> dict[str, tuple[int, int]]:
    snap: dict[str, tuple[int, int]] = {}
    for root in _download_roots():
        try:
            for p in root.iterdir():
                if not p.is_file():
                    continue
                st = p.stat()
                snap[str(p.resolve()).lower()] = (int(st.st_mtime_ns), int(st.st_size))
        except Exception:
            continue
    return snap


def _capture_new_download(before: dict[str, tuple[int, int]], output: Path, since: float) -> dict | None:
    candidates: list[tuple[float, Path, dict]] = []
    for root in _download_roots():
        try:
            files = list(root.iterdir())
        except Exception:
            continue
        for p in files:
            try:
                if not p.is_file() or p.suffix.lower() in {".crdownload", ".tmp", ".part"}:
                    continue
                st = p.stat()
                key = str(p.resolve()).lower()
                previous = before.get(key)
                changed = previous is None or previous != (int(st.st_mtime_ns), int(st.st_size))
                if not changed or st.st_mtime < since - 3 or st.st_size < 1024:
                    continue
                data = p.read_bytes()
                validation = _validate_blogger_theme_bytes(data)
                candidates.append((st.st_mtime, p, validation))
            except Exception:
                continue
    if not candidates:
        return None
    candidates.sort(key=lambda item: item[0], reverse=True)
    _, source, validation = candidates[0]
    output.parent.mkdir(parents=True, exist_ok=True)
    tmp = output.with_suffix(output.suffix + ".filesystem.tmp")
    shutil.copy2(source, tmp)
    _validate_blogger_theme_bytes(tmp.read_bytes())
    tmp.replace(output)
    validation.update({
        "capture_mode": "chrome-download-directory-fallback",
        "download_source_name": source.name,
    })
    return validation


def _wait_capture_new_download(page, before, output: Path, since: float, *, timeout_ms: int = 60_000):
    deadline = time.time() + max(1, timeout_ms) / 1000.0
    while time.time() < deadline:
        validation = _capture_new_download(before, output, since)
        if validation is not None:
            validation["filesystem_wait_ms"] = timeout_ms
            return validation
        page.wait_for_timeout(750)
    return None


def _capture_theme_from_responses(responses: list, output: Path) -> dict | None:
    for response in reversed(responses[-120:]):
        try:
            status = int(response.status)
            if status < 200 or status >= 400:
                continue
            url = str(response.url or "")
            if "blogger" not in url.lower() and "google" not in url.lower():
                continue
            headers = response.headers
            content_type = str(headers.get("content-type") or "").lower()
            disposition = str(headers.get("content-disposition") or "").lower()
            if not any(token in content_type for token in ("xml", "text", "octet-stream")) and "attachment" not in disposition:
                continue
            data = response.body()
            if len(data) > 8_000_000:
                continue
            try:
                return _write_validated_bytes(
                    data,
                    output,
                    "network-response-fallback",
                    response_url=url[:500],
                    response_content_type=content_type[:160],
                )
            except bp.SafeAutomationError:
                continue
        except Exception:
            continue
    return None


def execute_backup(expected_blog_id: str, output: str) -> dict:
    blog_id = str(expected_blog_id or "").strip()
    if not blog_id.isdigit():
        raise bp.SafeAutomationError("Blog ID esperado inválido.")
    out = Path(output).resolve()
    safe_cdp = bp.validate_cdp_url(bp.DEFAULT_CDP_URL, allow_remote=False)

    with sync_playwright() as pw:
        browser, context = bp.connect_official_chrome(pw, safe_cdp)
        page = ensure_theme_page(context, blog_id)
        page.wait_for_timeout(900)
        route = bp.sanitize_url(page.url)
        actual_id = extract_panel_blog_id(page.url)
        if actual_id != blog_id:
            raise bp.SafeAutomationError(
                f"Blog ID divergente antes do backup do tema: atual={actual_id!r}, esperado={blog_id!r}."
            )

        responses: list = []
        page.on("response", lambda response: responses.append(response))
        download_policy = _configure_cdp_downloads(context, page)
        before = _snapshot_downloads()
        started = time.time()
        _open_actions(page)
        item = _backup_item(page)
        validation = None
        try:
            with page.expect_download(timeout=12_000) as info:
                try:
                    item.click(timeout=5_000)
                except Exception:
                    item.evaluate("el => el.click()")
            validation = _save_download(info.value, out)
        except PlaywrightTimeoutError:
            validation = _wait_capture_new_download(page, before, out, started, timeout_ms=5_000)
            if validation is None:
                validation = _capture_theme_from_responses(responses, out)
            if validation is None:
                button = _wait_download_button(page, timeout_ms=20_000)
                if button is not None:
                    clicked_at = time.time()
                    try:
                        with page.expect_download(timeout=30_000) as info:
                            try:
                                button.click(timeout=8_000, force=True)
                            except Exception:
                                button.evaluate("el => el.click()")
                        validation = _save_download(info.value, out)
                    except PlaywrightTimeoutError:
                        validation = _wait_capture_new_download(
                            page, before, out, min(started, clicked_at), timeout_ms=20_000
                        )
                        if validation is None:
                            validation = _capture_theme_from_responses(responses, out)
            if validation is None:
                detail = _visible_backup_diagnostics(page)
                raise bp.SafeAutomationError(
                    "Fazer backup foi acionado, mas nenhum XML válido foi capturado por download, diretório ou resposta de rede. "
                    + (f"Diagnóstico: {detail}" if detail else "Sem controles visíveis adicionais.")
                )
        connected = browser.is_connected()

    return {
        "status": "BLOGGER_THEME_BACKUP_VALIDATED",
        "blog_id": blog_id,
        "output": str(out),
        "bytes": out.stat().st_size,
        "auto_route": route,
        "browser_connected": connected,
        "cdp_download_policy": download_policy,
        "controlled_download_dir": str(CONTROLLED_DOWNLOAD_DIR),
        **(validation or {}),
    }


def main() -> int:
    p = argparse.ArgumentParser(description="Abre a rota Tema do Blog ID e cria backup Blogger validado pelo Chrome oficial.")
    p.add_argument("--expected-blog-id", required=True)
    p.add_argument("--output", required=True)
    args = p.parse_args()
    result = execute_backup(args.expected_blog_id, args.output)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
