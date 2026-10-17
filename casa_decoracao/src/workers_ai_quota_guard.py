import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STATUS_PATH = ROOT / "casa_decoracao" / "data" / "workers_ai_status.json"
MODEL = os.getenv("CASA_AI_MODEL", "@cf/qwen/qwen3-30b-a3b-fp8").strip()


def save_status(payload):
    STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATUS_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def set_output(name, value):
    output = os.getenv("GITHUB_OUTPUT", "").strip()
    if output:
        with open(output, "a", encoding="utf-8") as fh:
            fh.write(f"{name}={value}\n")


def main():
    account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID", "").strip()
    token = os.getenv("CLOUDFLARE_API_TOKEN", "").strip()
    now = datetime.now(timezone.utc).isoformat()

    if not account_id or not token:
        save_status({
            "checked_at_utc": now,
            "available": False,
            "reason": "cloudflare_credentials_missing",
            "model": MODEL,
        })
        raise RuntimeError("CLOUDFLARE_ACCOUNT_ID/CLOUDFLARE_API_TOKEN ausentes")

    endpoint = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{MODEL}"
    body = json.dumps({
        "messages": [{"role": "user", "content": "Responda apenas OK"}],
        "max_tokens": 1,
        "temperature": 0,
    }).encode("utf-8")
    req = urllib.request.Request(endpoint, data=body, method="POST", headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "CasaEDecoracao-WorkersAI-QuotaGuard/1.0",
    })

    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            response.read()
        status = {
            "checked_at_utc": now,
            "available": True,
            "reason": "ok",
            "model": MODEL,
        }
        save_status(status)
        set_output("available", "true")
        set_output("reason", "ok")
        print("Workers AI disponível; geração liberada para esta execução.")
        return
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:3000]
        folded = detail.casefold()
        daily_quota = (
            exc.code == 429
            and (
                "daily free allocation" in folded
                or "10,000 neurons" in folded
                or "10000 neurons" in folded
                or '"code":4006' in folded.replace(" ", "")
                or "4006:" in folded
            )
        )

        if daily_quota:
            status = {
                "checked_at_utc": now,
                "available": False,
                "reason": "daily_free_allocation_exhausted",
                "http_status": exc.code,
                "model": MODEL,
                "reset": "00:00 UTC",
            }
            save_status(status)
            set_output("available", "false")
            set_output("reason", "daily_free_allocation_exhausted")
            print("Workers AI: cota gratuita diária esgotada. Geração e imagem serão puladas nesta execução; nova tentativa ocorrerá no próximo agendamento após o reset diário.")
            return

        if exc.code == 429:
            status = {
                "checked_at_utc": now,
                "available": False,
                "reason": "transient_rate_limit",
                "http_status": exc.code,
                "model": MODEL,
            }
            save_status(status)
            set_output("available", "false")
            set_output("reason", "transient_rate_limit")
            print("Workers AI: rate limit transitório. Execução de geração pulada para evitar retries agressivos.")
            return

        save_status({
            "checked_at_utc": now,
            "available": False,
            "reason": "cloudflare_http_error",
            "http_status": exc.code,
            "model": MODEL,
            "detail": detail[:500],
        })
        raise RuntimeError(f"Workers AI HTTP {exc.code}: {detail[:500]}") from exc


if __name__ == "__main__":
    main()
