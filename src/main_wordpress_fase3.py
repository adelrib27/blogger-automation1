import html
import json
import os
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import gerar_artigo
import gerar_pautas
import links_internos
import main as motor
import main_wordpress
import main_wordpress_auto


BASE_DIR = Path(__file__).resolve().parent.parent
CURRENT_PRODUCT_PATH = BASE_DIR / "data" / "fase3" / "produto_atual.json"
QUEUE_PATH = BASE_DIR / "data" / "fase3" / "fila_dia.json"
POLICY_PATH = BASE_DIR / "config" / "fase3_politica_editorial.json"


def carregar_json(caminho, padrao):
    try:
        dados = json.loads(caminho.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return padrao
    return dados


def salvar_json(caminho, dados):
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(
        json.dumps(dados, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def contexto_fase3():
    politica = carregar_json(POLICY_PATH, {})
    atual = carregar_json(CURRENT_PRODUCT_PATH, {})
    if not politica or not atual:
        raise RuntimeError("Contexto da Fase 3 não foi preparado antes da publicação.")

    fuso = ZoneInfo(str(politica.get("timezone") or "America/Sao_Paulo"))
    hoje = datetime.now(fuso).date().isoformat()
    if atual.get("date") != hoje:
        raise RuntimeError(
            f"Produto da Fase 3 está desatualizado: {atual.get('date')} != {hoje}."
        )

    modo = politica.get("phase3_mode") or {}
    ativacao = str(modo.get("activation_date") or "").strip()
    if ativacao and hoje < ativacao:
        raise RuntimeError(
            f"Fase 3 ainda não está ativa para publicação: início={ativacao}."
        )

    produto = atual.get("product") or {}
    obrigatorios = {
        "itemId": produto.get("itemId"),
        "productName": produto.get("productName"),
        "offerLink": produto.get("offerLink"),
        "category": atual.get("category"),
        "keyword": atual.get("keyword"),
        "time": atual.get("time"),
    }
    ausentes = [campo for campo, valor in obrigatorios.items() if not str(valor or "").strip()]
    if ausentes:
        raise RuntimeError(
            "Produto da Fase 3 incompleto: " + ", ".join(ausentes)
        )

    return politica, atual


def instalar_produto_da_fila(atual):
    produto = atual["product"]
    nome = str(produto["productName"]).strip()
    link = str(produto["offerLink"]).strip()
    categoria_fila = str(atual["category"]).strip()

    produto_catalogo = {
        "nome": nome,
        "link_afiliado": link,
        "ativo": True,
    }

    def carregar_produtos_fase3():
        return [dict(produto_catalogo)]

    gerar_pautas.carregar_produtos = carregar_produtos_fase3

    # A categoria validada pela camada semântica da fila é a autoridade final.
    def classificar_categoria_fase3(nome_produto, categoria_atual=""):
        if str(nome_produto or "").strip().casefold() == nome.casefold():
            return categoria_fila
        return categoria_fila

    main_wordpress.classificar_categoria_produto_wordpress = classificar_categoria_fase3

    preparar_original = motor.preparar_produto_principal

    def preparar_produto_fase3(produto_base):
        resultado = preparar_original(produto_base)
        resultado.update(
            {
                "shopee_item_id": str(produto.get("itemId") or ""),
                "shopee_shop_id": str(produto.get("shopId") or ""),
                "shopee_shop_name": str(produto.get("shopName") or ""),
                "shopee_keyword": str(atual.get("keyword") or ""),
                "shopee_category": categoria_fila,
                "seller_extra_commission_pct": produto.get("sellerExtraCommissionPct"),
                "total_commission_pct": produto.get("totalCommissionPct"),
                "rating_star": produto.get("ratingStar"),
            }
        )
        imagem = str(produto.get("imageUrl") or "").strip()
        if imagem.startswith("https://"):
            resultado.update(
                {
                    "imagem_produto": imagem,
                    "imagem_verificada": True,
                    "imagem_origem": "Shopee Affiliate Open API",
                }
            )
        return resultado

    motor.preparar_produto_principal = preparar_produto_fase3

    def enriquecer_produto_fase3(produto_base):
        resultado = dict(produto_base or {})
        imagem = str(produto.get("imageUrl") or "").strip()
        if imagem.startswith("https://"):
            resultado.update(
                {
                    "imagem_produto": imagem,
                    "imagem_verificada": True,
                    "imagem_origem": "Shopee Affiliate Open API",
                }
            )
        return resultado

    motor.enriquecer_produto_com_imagem = enriquecer_produto_fase3


def instalar_padrao_editorial_fase3(politica):
    editorial = politica.get("editorial") or {}
    minimo = int(editorial.get("word_count_min", 900))
    maximo = int(editorial.get("word_count_max", 1400))

    prompt_original = gerar_artigo.criar_prompt_artigo

    def criar_prompt_fase3(*args, **kwargs):
        prompt = prompt_original(*args, **kwargs)
        return (
            prompt
            + f"""

PADRÃO EDITORIAL ADICIONAL — FASE 3 RADAR TECH BR:
- Entregue entre {minimo} e {maximo} palavras de conteúdo editorial útil.
- Inclua, próximo ao início, um resumo rápido e objetivo para o leitor.
- Explique vantagens e limitações somente quando puder fazê-lo sem inventar dados.
- Inclua contexto de uso, para quem a solução pode fazer sentido e o que conferir antes da compra.
- Não diga nem sugira que o Radar Tech BR testou fisicamente o produto.
- Quando faltar um dado específico, use linguagem prudente e oriente a conferir o anúncio ou manual.
- Não preencha lacunas por inferência.
"""
        )

    gerar_artigo.criar_prompt_artigo = criar_prompt_fase3

    validar_original = main_wordpress.validar_pacote_wordpress

    def validar_pacote_fase3(pacote):
        resultado = validar_original(pacote)
        artigo = (pacote or {}).get("artigo") or {}
        conteudo = str(artigo.get("conteudo_html") or "")
        texto = re.sub(r"<[^>]+>", " ", conteudo)
        texto = html.unescape(texto)
        palavras = re.findall(r"\b[\wÀ-ÿ'-]+\b", texto, flags=re.UNICODE)
        quantidade = len(palavras)

        problemas = list(resultado.get("problemas") or [])
        if quantidade < minimo or quantidade > maximo:
            problemas.append(
                {
                    "tipo": "Extensão editorial fora da política da Fase 3",
                    "trecho": (
                        f"Artigo com {quantidade} palavras; política exige "
                        f"entre {minimo} e {maximo}."
                    ),
                }
            )

        return {
            **resultado,
            "aprovado": len(problemas) == 0,
            "problemas": problemas,
            "quantidade_problemas": len(problemas),
            "quantidade_palavras_fase3": quantidade,
        }

    main_wordpress.validar_pacote_wordpress = validar_pacote_fase3


def _termos_ancora(titulo, palavra_chave):
    genericos = {
        "como", "escolher", "antes", "comprar", "compra", "guia", "conferir",
        "verificar", "produto", "para", "com", "sem", "que", "uma", "um",
        "de", "da", "do", "das", "dos", "e", "em", "o", "a", "os", "as",
    }
    candidatos = []

    palavra_chave = str(palavra_chave or "").strip()
    if len(palavra_chave) >= 6:
        candidatos.append(palavra_chave)

    palavras = re.findall(r"[A-Za-zÀ-ÿ0-9+-]+", str(titulo or ""))
    for tamanho in (4, 3, 2):
        for inicio in range(0, max(0, len(palavras) - tamanho + 1)):
            trecho = palavras[inicio : inicio + tamanho]
            significativas = [p for p in trecho if p.casefold() not in genericos and len(p) >= 3]
            if len(significativas) < 2:
                continue
            frase = " ".join(trecho).strip()
            if len(frase) >= 9 and frase not in candidatos:
                candidatos.append(frase)

    candidatos.sort(key=len, reverse=True)
    return candidatos


def _inserir_ancora_html(conteudo_html, termos, url):
    partes_anchors = re.split(
        r"(<a\b[^>]*>.*?</a>)",
        conteudo_html,
        flags=re.IGNORECASE | re.DOTALL,
    )

    for termo in termos:
        padrao = re.compile(
            r"(?<![\wÀ-ÿ])" + re.escape(termo) + r"(?![\wÀ-ÿ])",
            flags=re.IGNORECASE,
        )
        for indice in range(0, len(partes_anchors), 2):
            segmentos = re.split(r"(<[^>]+>)", partes_anchors[indice])
            for posicao in range(0, len(segmentos), 2):
                if not padrao.search(segmentos[posicao]):
                    continue

                def substituir(match):
                    return (
                        f'<a href="{html.escape(url, quote=True)}">'
                        f'{match.group(0)}</a>'
                    )

                segmentos[posicao] = padrao.sub(substituir, segmentos[posicao], count=1)
                partes_anchors[indice] = "".join(segmentos)
                return "".join(partes_anchors), termo

    return conteudo_html, ""


def instalar_links_contextuais_fase3(politica):
    editorial = politica.get("editorial") or {}
    links_cfg = editorial.get("contextual_internal_links") or {}
    if not links_cfg.get("enabled", True):
        return

    limite_padrao = int(links_cfg.get("max_per_article", 3))

    def adicionar_links_contextuais(
        conteudo_html,
        titulo,
        palavra_chave,
        categoria="",
        limite=3,
    ):
        limite_real = min(int(limite or limite_padrao), limite_padrao)
        selecionados = links_internos.selecionar_links_internos(
            titulo=titulo,
            palavra_chave=palavra_chave,
            categoria=categoria,
            limite=max(limite_real * 4, limite_real),
        )
        historico = links_internos.carregar_historico()
        por_url = {
            str(item.get("url") or "").strip(): item
            for item in historico
            if isinstance(item, dict)
        }

        atualizado = conteudo_html
        aplicados = []
        for link in selecionados:
            if len(aplicados) >= limite_real:
                break
            url = str(link.get("url") or "").strip()
            item = por_url.get(url) or {}
            termos = _termos_ancora(
                item.get("titulo") or link.get("titulo"),
                item.get("palavra_chave"),
            )
            atualizado_novo, ancora = _inserir_ancora_html(atualizado, termos, url)
            if not ancora or atualizado_novo == atualizado:
                continue
            atualizado = atualizado_novo
            aplicados.append(
                {
                    "titulo": link.get("titulo"),
                    "url": url,
                    "pontuacao": link.get("pontuacao"),
                    "ancora": ancora,
                }
            )

        return {
            "conteudo_html": atualizado,
            "links": aplicados,
            "quantidade": len(aplicados),
        }

    motor.adicionar_links_internos = adicionar_links_contextuais


def instalar_historico_fase3(atual):
    registrar_original = main_wordpress.registrar_rascunho
    produto_fila = atual.get("product") or {}

    def registrar_rascunho_fase3(resultado, pacote):
        registrar_original(resultado, pacote)
        dados = main_wordpress.carregar_lista(main_wordpress.RASCUNHOS_WORDPRESS)
        post_id = resultado.get("id")
        for item in dados:
            if not isinstance(item, dict) or item.get("post_id") != post_id:
                continue
            item.update(
                {
                    "shopee_item_id": str(produto_fila.get("itemId") or ""),
                    "shopee_shop_id": str(produto_fila.get("shopId") or ""),
                    "shopee_shop_name": str(produto_fila.get("shopName") or ""),
                    "shopee_keyword": str(atual.get("keyword") or ""),
                    "fase3_slot": str(atual.get("time") or ""),
                }
            )
        main_wordpress.salvar_lista(main_wordpress.RASCUNHOS_WORDPRESS, dados)

    main_wordpress.registrar_rascunho = registrar_rascunho_fase3


def atualizar_status_fila(atual, status, resultado=None, erro=""):
    fila = carregar_json(QUEUE_PATH, {})
    if not fila:
        return

    agora = datetime.now(ZoneInfo(str(fila.get("timezone") or "America/Sao_Paulo"))).isoformat()
    for slot in fila.get("slots") or []:
        if str(slot.get("time")) != str(atual.get("time")):
            continue
        item_fila = str((slot.get("product") or {}).get("itemId") or "")
        item_atual = str((atual.get("product") or {}).get("itemId") or "")
        if item_fila != item_atual:
            continue
        slot["status"] = status
        slot["updatedAt"] = agora
        if resultado:
            wordpress = resultado.get("wordpress") or {}
            slot["wordpress"] = {
                "postId": wordpress.get("id"),
                "url": wordpress.get("url"),
                "status": wordpress.get("status"),
            }
        if erro:
            slot["lastError"] = str(erro)[:500]
        break

    salvar_json(QUEUE_PATH, fila)


def executar():
    politica, atual = contexto_fase3()
    os.environ["RADAR_PHASE3_ACTIVE"] = "1"
    os.environ["RADAR_PHASE3_SLOT"] = str(atual.get("time") or "")

    instalar_produto_da_fila(atual)
    instalar_padrao_editorial_fase3(politica)
    instalar_links_contextuais_fase3(politica)
    instalar_historico_fase3(atual)

    print("=== RADAR TECH BR — FASE 3 / PUBLICAÇÃO DE SLOT ===")
    print("Slot:", atual.get("time"))
    print("Categoria:", atual.get("category"))
    print("Keyword:", atual.get("keyword"))
    print("Produto:", (atual.get("product") or {}).get("productName"))

    try:
        resultado = main_wordpress_auto.executar()
        if not isinstance(resultado, dict):
            raise RuntimeError("Publicação da Fase 3 não retornou resultado válido.")
        atualizar_status_fila(atual, "PUBLICADO", resultado=resultado)
        print("Fila da Fase 3 atualizada para PUBLICADO.")
        return resultado
    except Exception as erro:
        atualizar_status_fila(atual, "QUARENTENA", erro=str(erro))
        print("Slot enviado para QUARENTENA após falha do pipeline.")
        raise


if __name__ == "__main__":
    executar()
