import json
import os
import re
import sys
import urllib.error
import urllib.request


MODEL = "@cf/qwen/qwen3-30b-a3b-fp8"


def required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Secret ausente: {name}")
    return value


def validar_account_id(account_id: str) -> str:
    if not re.fullmatch(r"[a-fA-F0-9]{32}", account_id):
        raise RuntimeError(
            "RADAR_CLOUDFLARE_ACCOUNT_ID inválido: esperado exatamente "
            "32 caracteres hexadecimais, sem espaços, rótulos ou quebras de linha."
        )
    return account_id


def main() -> None:
    account_id = validar_account_id(required_env("RADAR_CLOUDFLARE_ACCOUNT_ID"))
    api_token = required_env("RADAR_CLOUDFLARE_API_TOKEN")

    url = (
        "https://api.cloudflare.com/client/v4/accounts/"
        f"{account_id}/ai/run/{MODEL}"
    )

    payload = {
        "messages": [
            {
                "role": "system",
                "content": "Responda de forma curta em português do Brasil.",
            },
            {
                "role": "user",
                "content": "Responda apenas: RADAR_OK",
            },
        ],
        "max_tokens": 32,
        "temperature": 0,
    }

    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            status = response.status
            body = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        safe_body = exc.read().decode("utf-8", errors="replace")[:1200]
        raise RuntimeError(
            f"Cloudflare respondeu HTTP {exc.code}. Corpo seguro: {safe_body}"
        ) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Falha de conexão com Cloudflare: {exc.reason}") from exc

    if status != 200:
        raise RuntimeError(f"Cloudflare respondeu HTTP inesperado: {status}")

    try:
        data = json.loads(body)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Cloudflare retornou resposta não JSON.") from exc

    if not data.get("success", False):
        errors = data.get("errors") or []
        raise RuntimeError(f"Cloudflare informou falha: {errors}")

    result = data.get("result")
    text = ""
    if isinstance(result, dict):
        text = str(result.get("response") or result.get("text") or "").strip()
    elif isinstance(result, str):
        text = result.strip()

    print("SUCESSO: credenciais RADAR_CLOUDFLARE_* autenticaram no Workers AI.")
    print(f"Modelo validado: {MODEL}")
    if text:
        print("Resposta curta recebida do modelo.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        sys.exit(1)
