import json
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
PAYLOAD_PATH = BASE_DIR / "artifacts" / "social_payload.json"
ESTADO_PATH = BASE_DIR / "data" / "social_publicados.json"
RESULTADO_PATH = BASE_DIR / "artifacts" / "facebook_publish_result.json"

GRAPH_VERSION = os.getenv("FACEBOOK_GRAPH_VERSION", "v26.0").strip() or "v26.0"
GRAPH_BASE = f"https://graph.facebook.com/{GRAPH_VERSION}"


def agora_iso():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def carregar_json(path, padrao):
    if not path.exists():
        return padrao
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return padrao


def salvar_json(path, dados):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(dados, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def graph_request(method, path, token, params=None):
    params = params or {}
    url = f"{GRAPH_BASE}/{path.lstrip('/')}"
    headers = {"Authorization": f"Bearer {token}"}
    data = None

    if method == "GET":
        if params:
            url += "?" + urllib.parse.urlencode(params)
    elif method == "POST":
        data = urllib.parse.urlencode(params).encode("utf-8")
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    else:
        raise RuntimeError(f"Método Graph não suportado: {method}")

    requisicao = urllib.request.Request(url, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(requisicao, timeout=30) as resposta:
            corpo = resposta.read().decode("utf-8")
    except urllib.error.HTTPError as erro:
        corpo = erro.read().decode("utf-8", errors="replace")
        try:
            detalhe = json.loads(corpo)
        except json.JSONDecodeError:
            detalhe = {"message": corpo[:500]}
        raise RuntimeError(
            f"Graph API retornou HTTP {erro.code}: "
            + json.dumps(detalhe, ensure_ascii=False)
        ) from erro
    except urllib.error.URLError as erro:
        raise RuntimeError(f"Falha de conexão com a Graph API: {erro.reason}") from erro

    try:
        return json.loads(corpo)
    except json.JSONDecodeError as erro:
        raise RuntimeError("Resposta inválida da Graph API.") from erro


def encontrar_estado(estado, post_id):
    for item in estado:
        if not isinstance(item, dict):
            continue
        if str(item.get("post_id") or "") != post_id:
            continue
        if str(item.get("network") or "").lower() != "facebook":
            continue
        if item.get("status") in {"published", "remote_already_present"}:
            return item
    return None


def registrar_estado(estado, registro):
    post_id = str(registro.get("post_id") or "")
    novo = []
    substituiu = False

    for item in estado:
        if (
            isinstance(item, dict)
            and str(item.get("post_id") or "") == post_id
            and str(item.get("network") or "").lower() == "facebook"
        ):
            if not substituiu:
                novo.append(registro)
                substituiu = True
            continue
        novo.append(item)

    if not substituiu:
        novo.append(registro)

    return novo


def procurar_post_remoto(page_id, token, artigo_url):
    resposta = graph_request(
        "GET",
        f"{page_id}/posts",
        token,
        {
            "fields": "id,message,permalink_url,created_time",
            "limit": 50,
        },
    )

    for item in resposta.get("data", []):
        mensagem = str(item.get("message") or "")
        if artigo_url and artigo_url in mensagem:
            return item
    return None


def main():
    print("=== FACEBOOK — PUBLICAÇÃO CONTROLADA ===")

    aprovacao = str(os.getenv("FACEBOOK_PUBLISH_APPROVED") or "").strip()
    if aprovacao != "SIM_PUBLICAR":
        raise RuntimeError("Publicação bloqueada: confirmação explícita ausente.")

    page_id = str(os.getenv("FACEBOOK_PAGE_ID") or "").strip()
    token = str(os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN") or "").strip()
    esperado = str(os.getenv("FACEBOOK_EXPECTED_BLOGGER_POST_ID") or "").strip()

    if not page_id:
        raise RuntimeError("FACEBOOK_PAGE_ID ausente.")
    if not token:
        raise RuntimeError("FACEBOOK_PAGE_ACCESS_TOKEN ausente.")
    if not esperado:
        raise RuntimeError("FACEBOOK_EXPECTED_BLOGGER_POST_ID ausente.")

    payload = carregar_json(PAYLOAD_PATH, {})
    if not payload or payload.get("status") == "sem_post_novo":
        raise RuntimeError("Nenhum post elegível foi preparado para publicação.")

    post = payload.get("post") or {}
    facebook = payload.get("facebook") or {}

    post_id = str(post.get("id") or "").strip()
    titulo = str(post.get("title") or "").strip()
    artigo_url = str(post.get("url") or "").strip()
    mensagem = str(facebook.get("text") or "").strip()
    link = str(facebook.get("link") or artigo_url).strip()

    if post_id != esperado:
        raise RuntimeError(
            "Trava de segurança acionada: o post preparado não é o post aprovado."
        )
    if not mensagem or not artigo_url or not link:
        raise RuntimeError("Payload do Facebook incompleto.")

    estado = carregar_json(ESTADO_PATH, [])
    if not isinstance(estado, list):
        estado = []

    existente_local = encontrar_estado(estado, post_id)
    if existente_local:
        resultado = {
            "status": "already_recorded",
            "network": "facebook",
            "blogger_post_id": post_id,
            "title": titulo,
            "blog_url": artigo_url,
            "social_post_id": existente_local.get("social_post_id"),
            "permalink_url": existente_local.get("permalink_url"),
            "published_new_post": False,
        }
        salvar_json(RESULTADO_PATH, resultado)
        print("Publicação já registrada localmente; nenhuma nova postagem feita.")
        return

    pagina = graph_request(
        "GET",
        page_id,
        token,
        {"fields": "id,name,link"},
    )

    if str(pagina.get("id") or "") != page_id:
        raise RuntimeError("A Página retornada pela Meta não corresponde ao PAGE_ID configurado.")

    remoto = procurar_post_remoto(page_id, token, artigo_url)
    if remoto:
        registro = {
            "post_id": post_id,
            "network": "facebook",
            "status": "remote_already_present",
            "blog_url": artigo_url,
            "title": titulo,
            "target_page_name": pagina.get("name"),
            "social_post_id": remoto.get("id"),
            "permalink_url": remoto.get("permalink_url"),
            "published_at": remoto.get("created_time"),
            "recorded_at": agora_iso(),
        }
        estado = registrar_estado(estado, registro)
        salvar_json(ESTADO_PATH, estado)
        salvar_json(
            RESULTADO_PATH,
            {
                **registro,
                "published_new_post": False,
                "note": "O artigo já estava presente na Página; nenhuma duplicação foi criada.",
            },
        )
        print("O artigo já estava publicado na Página; registro local sincronizado.")
        return

    resposta = graph_request(
        "POST",
        f"{page_id}/feed",
        token,
        {
            "message": mensagem,
            "link": link,
        },
    )

    social_post_id = str(resposta.get("id") or "").strip()
    if not social_post_id:
        raise RuntimeError("A Meta não retornou o ID do post publicado.")

    verificacao = graph_request(
        "GET",
        social_post_id,
        token,
        {"fields": "id,permalink_url,created_time"},
    )

    registro = {
        "post_id": post_id,
        "network": "facebook",
        "status": "published",
        "blog_url": artigo_url,
        "title": titulo,
        "target_page_name": pagina.get("name"),
        "social_post_id": social_post_id,
        "permalink_url": verificacao.get("permalink_url"),
        "published_at": verificacao.get("created_time"),
        "recorded_at": agora_iso(),
    }

    estado = registrar_estado(estado, registro)
    salvar_json(ESTADO_PATH, estado)
    salvar_json(
        RESULTADO_PATH,
        {
            **registro,
            "published_new_post": True,
        },
    )

    print("Página:", pagina.get("name"))
    print("Artigo:", titulo)
    print("Facebook post ID:", social_post_id)
    print("Permalink:", verificacao.get("permalink_url") or "não retornado")
    print("FACEBOOK: PUBLICAÇÃO CONCLUÍDA.")


if __name__ == "__main__":
    main()
