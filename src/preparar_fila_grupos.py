import hashlib
import json
import os
import re
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config" / "facebook_grupos.json"
GRUPOS_PATH = BASE_DIR / "data" / "facebook_grupos.json"
FILA_PATH = BASE_DIR / "data" / "facebook_fila_grupos.json"
HISTORICO_PATH = BASE_DIR / "data" / "facebook_grupos_publicados.json"
RESULTADO_PATH = BASE_DIR / "artifacts" / "facebook_grupos_queue_result.json"

ESCOPO_BLOGGER = "https://www.googleapis.com/auth/blogger"
TITULOS_INSTITUCIONAIS = {
    "política de privacidade",
    "politica de privacidade",
    "termos de uso",
    "sobre",
    "sobre nós",
    "sobre nos",
    "contato",
}


def carregar_json(path, padrao):
    if not path.exists():
        return padrao
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return padrao


def salvar_json(path, dados):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def normalizar(texto):
    texto = unicodedata.normalize("NFKD", str(texto or ""))
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = re.sub(r"[^a-zA-Z0-9]+", " ", texto).lower()
    return re.sub(r"\s+", " ", texto).strip()


def criar_servico_blogger():
    nomes = ["BLOGGER_REFRESH_TOKEN", "BLOGGER_CLIENT_ID", "BLOGGER_CLIENT_SECRET", "BLOGGER_BLOG_ID"]
    ausentes = [nome for nome in nomes if not os.getenv(nome)]
    if ausentes:
        raise RuntimeError("Variáveis ausentes: " + ", ".join(ausentes))
    credenciais = Credentials(
        token=None,
        refresh_token=os.environ["BLOGGER_REFRESH_TOKEN"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["BLOGGER_CLIENT_ID"],
        client_secret=os.environ["BLOGGER_CLIENT_SECRET"],
        scopes=[ESCOPO_BLOGGER],
    )
    return build("blogger", "v3", credentials=credenciais, cache_discovery=False)


def agora_local(config):
    zona = ZoneInfo(config.get("timezone") or "America/Recife")
    return datetime.now(timezone.utc).astimezone(zona)


def grupo_chave(grupo):
    base = str(grupo.get("id") or grupo.get("url") or grupo.get("nome") or "").strip()
    return hashlib.sha1(base.encode("utf-8")).hexdigest()[:16]


def grupo_elegivel(grupo, post, config):
    if not grupo.get("ativo", True):
        return False
    temas = [normalizar(t) for t in (grupo.get("temas") or []) if normalizar(t)]
    if not temas:
        return bool((config.get("matching") or {}).get("allow_groups_without_themes", True))
    genericos = {normalizar(t) for t in ((config.get("matching") or {}).get("generic_themes") or [])}
    if any(t in genericos for t in temas):
        return True
    contexto = normalizar(" ".join([str(post.get("title") or ""), *[str(x) for x in (post.get("labels") or [])]]))
    return any(t in contexto or contexto in t for t in temas)


def limitar(texto, limite=300):
    texto = re.sub(r"\s+", " ", str(texto or "")).strip()
    if len(texto) <= limite:
        return texto
    corte = texto[: limite - 1]
    if " " in corte:
        corte = corte.rsplit(" ", 1)[0]
    return corte.rstrip(".,;:!?") + "…"


def resumo_post(conteudo):
    texto = re.sub(r"<script\b[^>]*>.*?</script>", " ", conteudo or "", flags=re.I | re.S)
    texto = re.sub(r"<style\b[^>]*>.*?</style>", " ", texto, flags=re.I | re.S)
    texto = re.sub(r"<[^>]+>", " ", texto)
    return limitar(texto, 230)


def primeira_imagem(conteudo):
    m = re.search(r"<img\b[^>]*?\bsrc=[\"']([^\"']+)[\"']", conteudo or "", flags=re.I)
    return m.group(1).strip() if m else ""


def gerar_texto(post, indice):
    titulo = str(post.get("title") or "").strip()
    url = str(post.get("url") or "").strip()
    resumo = resumo_post(str(post.get("content") or ""))
    modelos = [
        f"Quem está pesquisando sobre {titulo.lower()}? Este guia reúne pontos importantes para observar antes de escolher.\n\n{url}",
        f"Uma dúvida comum na hora de cuidar da casa é saber o que realmente vale observar antes de escolher. Este conteúdo sobre {titulo.lower()} pode ajudar:\n\n{url}",
        f"Antes de decidir, vale comparar instalação, uso no dia a dia e o que faz sentido para o ambiente. Separei este guia sobre {titulo.lower()}:\n\n{url}",
        f"Para quem gosta de soluções práticas para casa: este artigo explica de forma simples o que considerar sobre {titulo.lower()}.\n\n{url}",
        f"Vale a pena olhar alguns detalhes antes de escolher. O guia abaixo resume os principais pontos sobre {titulo.lower()} e pode ajudar na pesquisa:\n\n{url}",
        f"Quem já pesquisou algo parecido para casa? Este conteúdo traz uma visão prática sobre {titulo.lower()}.\n\n{limitar(resumo, 160)}\n\n{url}",
    ]
    base = modelos[indice % len(modelos)]
    return base + "\n\n#AchadosParaCasa #CasaEDecoracao #CasaeDecoração"


def buscar_posts(blogger, blog_id):
    resposta = blogger.posts().list(blogId=blog_id, status=["LIVE"], fetchBodies=True, maxResults=50).execute()
    posts = resposta.get("items", [])
    posts = [p for p in posts if str(p.get("title") or "").strip().lower() not in TITULOS_INSTITUCIONAIS]
    posts.sort(key=lambda p: str(p.get("published") or ""), reverse=True)
    return posts


def contagem_grupo(historico):
    return Counter(str(item.get("group_key") or "") for item in historico if isinstance(item, dict))


def ultima_data_grupo(historico):
    saida = {}
    for item in historico:
        if not isinstance(item, dict):
            continue
        chave = str(item.get("group_key") or "")
        data = str(item.get("published_at") or item.get("recorded_at") or "")
        if chave and data > saida.get(chave, ""):
            saida[chave] = data
    return saida


def main():
    print("=== FACEBOOK GRUPOS — FILA ASSISTIDA ===")
    print("Nenhuma publicação em grupo será feita pela API.\n")

    config = carregar_json(CONFIG_PATH, {})
    if config.get("publish_external") is not False or config.get("mode") != "assisted_only":
        raise RuntimeError("Configuração insegura: a fila de grupos deve permanecer em assisted_only e publish_external=false.")

    grupos = carregar_json(GRUPOS_PATH, [])
    fila = carregar_json(FILA_PATH, [])
    historico = carregar_json(HISTORICO_PATH, [])
    if not isinstance(grupos, list) or not isinstance(fila, list) or not isinstance(historico, list):
        raise RuntimeError("Arquivos de grupos/fila/histórico precisam conter listas JSON.")

    ativos = [g for g in grupos if isinstance(g, dict) and g.get("ativo", True) and g.get("nome") and g.get("url")]
    if not ativos:
        resultado = {"status": "sem_grupos_cadastrados", "created": 0, "safety": {"publish_external": False}}
        salvar_json(RESULTADO_PATH, resultado)
        print("Nenhum grupo ativo cadastrado ainda.")
        return

    blogger = criar_servico_blogger()
    posts = buscar_posts(blogger, os.environ["BLOGGER_BLOG_ID"])
    hoje = agora_local(config).date().isoformat()
    limite_dia = int(config.get("max_groups_per_article_per_day", 3))
    limite_pendente = int(config.get("max_pending_per_article", 3))

    publicados = {(str(i.get("post_id") or ""), str(i.get("group_key") or "")) for i in historico if isinstance(i, dict) and i.get("status") == "published"}
    pendentes = {(str(i.get("post_id") or ""), str(i.get("group_key") or "")) for i in fila if isinstance(i, dict) and i.get("status") == "pending"}
    usos = contagem_grupo(historico)
    ultimos = ultima_data_grupo(historico)

    escolhido = None
    elegiveis = []
    for post in posts:
        post_id = str(post.get("id") or "")
        candidatos = []
        for grupo in ativos:
            chave = grupo_chave(grupo)
            if not grupo_elegivel(grupo, post, config):
                continue
            if (post_id, chave) in publicados or (post_id, chave) in pendentes:
                continue
            candidatos.append(grupo)
        if candidatos:
            escolhido = post
            elegiveis = candidatos
            break

    if not escolhido:
        resultado = {"status": "sem_oportunidades_novas", "created": 0, "safety": {"publish_external": False}}
        salvar_json(RESULTADO_PATH, resultado)
        print("Nenhuma combinação nova de artigo + grupo encontrada.")
        return

    post_id = str(escolhido.get("id") or "")
    pendentes_post = [i for i in fila if isinstance(i, dict) and i.get("status") == "pending" and str(i.get("post_id") or "") == post_id]
    if len(pendentes_post) >= limite_pendente:
        resultado = {"status": "aguardando_publicacoes_pendentes", "post_id": post_id, "pending": len(pendentes_post), "created": 0, "safety": {"publish_external": False}}
        salvar_json(RESULTADO_PATH, resultado)
        print("Já existem itens pendentes suficientes para este artigo.")
        return

    usados_hoje = 0
    for item in fila + historico:
        if not isinstance(item, dict):
            continue
        if str(item.get("post_id") or "") == post_id and str(item.get("batch_date") or "") == hoje:
            usados_hoje += 1
    vagas_dia = max(0, limite_dia - usados_hoje)
    vagas_pendentes = max(0, limite_pendente - len(pendentes_post))
    quantidade = min(vagas_dia, vagas_pendentes, len(elegiveis))
    if quantidade <= 0:
        resultado = {"status": "limite_diario_atingido", "post_id": post_id, "batch_date": hoje, "created": 0, "safety": {"publish_external": False}}
        salvar_json(RESULTADO_PATH, resultado)
        print("Limite diário de grupos para este artigo já foi atingido.")
        return

    elegiveis.sort(key=lambda g: (int(g.get("prioridade", 2)), usos.get(grupo_chave(g), 0), ultimos.get(grupo_chave(g), ""), str(g.get("nome") or "")))
    selecionados = elegiveis[:quantidade]
    criados = []
    for indice, grupo in enumerate(selecionados):
        chave = grupo_chave(grupo)
        queue_id = hashlib.sha1(f"{post_id}|{chave}".encode("utf-8")).hexdigest()[:20]
        texto = gerar_texto(escolhido, usos.get(chave, 0) + indice)
        entrada = {
            "queue_id": queue_id,
            "status": "pending",
            "created_at": agora_local(config).isoformat(),
            "batch_date": hoje,
            "post_id": post_id,
            "post": {
                "title": escolhido.get("title"),
                "url": escolhido.get("url"),
                "labels": escolhido.get("labels") or [],
                "featured_image_url": primeira_imagem(str(escolhido.get("content") or "")),
            },
            "group_key": chave,
            "group": {
                "id": grupo.get("id"),
                "nome": grupo.get("nome"),
                "url": grupo.get("url"),
                "temas": grupo.get("temas") or [],
                "prioridade": grupo.get("prioridade", 2),
            },
            "copy": {
                "variation": (usos.get(chave, 0) + indice) % int(config.get("default_variations", 6)) + 1,
                "text": texto,
            },
            "manual_action_required": True,
        }
        fila.append(entrada)
        criados.append(entrada)

    salvar_json(FILA_PATH, fila)
    salvar_json(RESULTADO_PATH, {
        "status": "fila_atualizada",
        "created": len(criados),
        "post_id": post_id,
        "post_title": escolhido.get("title"),
        "batch_date": hoje,
        "queue_ids": [i["queue_id"] for i in criados],
        "safety": {"publish_external": False, "manual_action_required": True},
    })

    print("Artigo:", escolhido.get("title"))
    print("Itens criados:", len(criados))
    for item in criados:
        print("-", item["group"]["nome"], "->", item["queue_id"])
    print("\nFILA DE GRUPOS: OK — nenhuma publicação externa realizada.")


if __name__ == "__main__":
    main()
