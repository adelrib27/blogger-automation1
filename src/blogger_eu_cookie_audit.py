from __future__ import annotations

import argparse
import asyncio
import json
import re
from pathlib import Path
from urllib.parse import urlencode, urlsplit, urlunsplit, parse_qsl

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

BLOGS = [
    ("Eletroportáteis na Cozinha", "https://eletroportateis-na-cozinha.blogspot.com/"),
    ("Cabelos em Foco", "https://cabelos-em-foco.blogspot.com/"),
    ("Achados para Casa", "https://achadosparacasa2026.blogspot.com/"),
    ("Ventiladores em Foco", "https://ventiladores-em-foco.blogspot.com/"),
    ("Air Fryers em Foco", "https://air-fryers-em-foco.blogspot.com/"),
    ("Limpeza Inteligente", "https://limpeza-inteligente.blogspot.com/"),
    ("Conecta Achados", "https://conectaachados.blogspot.com/"),
    ("Estilo no Dia a Dia", "https://estilo-no-dia-a-dia-0071220800-2.blogspot.com/"),
    ("Casa em Ordem", "https://casa-em-ordem-pratica.blogspot.com/"),
    ("Escolha Certa Online", "https://escolha-certa-online.blogspot.com/"),
    ("Achados que Valem", "https://achados-que-valem.blogspot.com/"),
    ("Guia de Achados & Ofertas", "https://guia-de-achados-e-ofertas.blogspot.com/"),
    ("Vitrine Prática", "https://vitrine-pratica.blogspot.com/"),
    ("Moda e Ofertas", "https://moda-ofertas.blogspot.com/"),
    ("Achadinhos de Beleza", "https://canal-attitude.blogspot.com/"),
    ("Radar Tech BR", "https://portalradartechbr.blogspot.com/"),
    ("Cozinha Sem Complicação", "https://cozinha-sem-complicacao.blogspot.com/"),
    ("Liquidificadores em Foco", "https://liquidificadores-em-foco.blogspot.com/"),
]

BANNER_SELECTORS = [
    "#cookieChoiceInfo",
    ".cookie-choices-info",
    "[id*='cookieChoiceInfo']",
    "[class*='cookie-choices']",
]

DISMISS_SELECTORS = [
    "#cookieChoiceDismiss",
    ".cookie-choices-button",
    "[id*='cookieChoiceDismiss']",
]

COOKIE_TEXT_RE = re.compile(
    r"cookie|cookies|témoins|utilise des cookies|uses cookies|usa cookies|utiliza cookies",
    re.IGNORECASE,
)


def with_gl_fr(url: str) -> str:
    parts = urlsplit(url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query["gl"] = "fr"
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def slugify(text: str) -> str:
    value = text.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "blog"


async def first_visible(page, selectors: list[str]):
    for selector in selectors:
        locator = page.locator(selector).first
        try:
            if await locator.count() and await locator.is_visible(timeout=500):
                return locator, selector
        except Exception:
            pass
    return None, None


async def audit_blog(browser, semaphore: asyncio.Semaphore, name: str, base_url: str, out_dir: Path) -> dict:
    async with semaphore:
        context = await browser.new_context(
            locale="fr-FR",
            timezone_id="Europe/Paris",
            viewport={"width": 1440, "height": 1100},
            extra_http_headers={"Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8"},
        )
        page = await context.new_page()
        page.set_default_timeout(3000)
        page.set_default_navigation_timeout(12000)

        target = with_gl_fr(base_url)
        slug = slugify(name)
        before = out_dir / f"{slug}-before.png"
        after = out_dir / f"{slug}-after.png"

        result = {
            "name": name,
            "base_url": base_url,
            "target_url": target,
            "reachable": False,
            "http_status": None,
            "final_url": None,
            "banner_visible": False,
            "banner_selector": None,
            "banner_text": "",
            "dismiss_visible": False,
            "dismiss_selector": None,
            "dismiss_worked": False,
            "cookie_text_detected": False,
            "before_screenshot": str(before),
            "after_screenshot": str(after),
            "error": "",
        }

        try:
            response = await page.goto(target, wait_until="domcontentloaded", timeout=12000)
            result["http_status"] = response.status if response else None
            result["reachable"] = bool(response is None or response.ok)
            await page.wait_for_timeout(1500)
            result["final_url"] = page.url

            banner, banner_selector = await first_visible(page, BANNER_SELECTORS)
            result["banner_visible"] = banner is not None
            result["banner_selector"] = banner_selector

            if banner is not None:
                try:
                    text = (await banner.inner_text(timeout=1500)).strip()
                except Exception:
                    text = ""
                result["banner_text"] = re.sub(r"\s+", " ", text)[:1200]
                result["cookie_text_detected"] = bool(COOKIE_TEXT_RE.search(result["banner_text"]))
            else:
                body_text = await page.locator("body").inner_text(timeout=2000)
                result["cookie_text_detected"] = bool(COOKIE_TEXT_RE.search(body_text))

            await page.screenshot(path=str(before), full_page=True)

            dismiss, dismiss_selector = await first_visible(page, DISMISS_SELECTORS)
            result["dismiss_visible"] = dismiss is not None
            result["dismiss_selector"] = dismiss_selector

            if dismiss is None:
                for text in ["OK", "J'ACCEPTE", "ACCEPTER", "ENTENDI", "ACEITAR"]:
                    candidate = page.get_by_text(text, exact=True).first
                    try:
                        if await candidate.count() and await candidate.is_visible(timeout=300):
                            dismiss = candidate
                            result["dismiss_visible"] = True
                            result["dismiss_selector"] = f"text={text}"
                            break
                    except Exception:
                        pass

            if dismiss is not None:
                await dismiss.click(timeout=3000)
                await page.wait_for_timeout(500)
                banner_after, _ = await first_visible(page, BANNER_SELECTORS)
                result["dismiss_worked"] = banner_after is None

            await page.screenshot(path=str(after), full_page=True)

        except PlaywrightTimeoutError as exc:
            result["error"] = f"timeout: {exc}"
        except Exception as exc:
            result["error"] = f"{type(exc).__name__}: {exc}"
        finally:
            await context.close()

        result["pass"] = bool(
            result["reachable"]
            and result["banner_visible"]
            and result["cookie_text_detected"]
            and result["dismiss_visible"]
            and result["dismiss_worked"]
        )
        return result


async def run_audit(out_dir: Path) -> list[dict]:
    semaphore = asyncio.Semaphore(6)
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        try:
            tasks = [audit_blog(browser, semaphore, name, url, out_dir) for name, url in BLOGS]
            return await asyncio.gather(*tasks)
        finally:
            await browser.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Audita aviso europeu de cookies nos blogs Blogger.")
    parser.add_argument("--output", default="data/blogger_eu_cookie_audit", help="Diretório de saída")
    parser.add_argument("--strict", action="store_true", help="Falha se qualquer blog não passar")
    args = parser.parse_args()

    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    results = asyncio.run(run_audit(out_dir))
    results.sort(key=lambda item: item["name"].casefold())

    for result in results:
        state = "PASS" if result["pass"] else "FAIL"
        print(
            f"[{state}] {result['name']}: http={result['http_status']} "
            f"banner={result['banner_visible']} dismiss={result['dismiss_visible']} "
            f"dismiss_worked={result['dismiss_worked']} final={result['final_url']}"
        )
        if result["banner_text"]:
            print("  banner:", result["banner_text"][:240])
        if result["error"]:
            print("  erro:", result["error"])

    passed = sum(1 for item in results if item["pass"])
    failed = len(results) - passed
    report = {
        "version": 2,
        "mode": "SAFE_READ_ONLY",
        "region_hint": "gl=fr",
        "locale": "fr-FR",
        "concurrency": 6,
        "total": len(results),
        "passed": passed,
        "failed": failed,
        "results": results,
    }
    (out_dir / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Resumo: total={len(results)} pass={passed} fail={failed}")

    if args.strict and failed:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
