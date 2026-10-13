import json
import os
import re
import unicodedata
from pathlib import Path

import gerar_artigo
import gerar_pautas
import links_internos
import main as motor
import pautas
from validacao_wordpress import (
    instalar_regras_pauta_wordpress,
    instalar_regras_prompt_wordpress,
    validar_pacote_wordpress,
)
from wordpress_api import criar_post_rascunho


BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_WORDPRESS = BASE_DIR / "config" / "wordpress.json"
HISTORICO_WORDPRESS = BASE_DIR / "data" / "wordpress_historico.json"
RASCUNHOS_WORDPRESS = BASE_DIR / "data" / "wordpress_rascunhos.json"


def carregar_config_wordpress():
    try:
        with CONFIG_WORDPRESS.open("r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
    except (OSError, json.JSONDecodeError):
        return {}

    return dados if isinstance(dados, dict) else {}


CONFIG = carregar_config_wordpress()
URL_WORDPRESS = str(CONFIG.get("url_blog") or "").strip().rstrip("/") + "/"


# Isola o Radar Tech BR do histórico, rascunhos e URLs do Blogger.
motor.CONFIG_PATH = CONFIG_WORDPRESS
motor.HISTORICO_PATH = HISTORICO_WORDPRESS
pautas.ARQUIVO_HISTORICO = HISTORICO_WORDPRESS
pautas.ARQUIVO_RASCUNHOS = RASCUNHOS_WORDPRESS
links_internos.HISTORICO_PATH = HISTORICO_WORDPRESS

# O WordPress recebe regras editoriais e de pauta próprias,
# sem alterar o comportamento normal do Blogger.
instalar_regras_prompt_wordpress(gerar_artigo)
instalar_regras_pauta_wordpress(gerar_pautas)


# O seletor legado de complementares usa similaridade textual e, com um
# catálogo multitemático, pode cruzar categorias (ex.: lâmina de cabelo x
# lâmina de cozinha). No WordPress, mantemos só o produto principal até haver
# classificação por categoria/família de produto. O Blogger não é alterado.
def selecionar_complementares_wordpress_seguro(*args, **kwargs):
    return []


motor.selecionar_complementares = selecionar_complementares_wordpress_seguro


def _tokens_busca(texto):
    texto = str(texto or "").casefold()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(
        caractere
        for caractere in texto
        if unicodedata.category(caractere) != "Mn"
    )
    return {
        token
        for token in re.findall(r"[a-z0-9]+", texto)
        if len(token) >= 3
    }


def instalar_priorizacao_produto_teste():
    """
    Permite direcionar um teste manual para um produto/categoria sem alterar
    o catálogo. Sem a variável, a seleção continua aleatória como antes.
    """
    filtro = os.getenv("RADARTECH_TEST_PRODUCT_KEYWORD", "").strip()

    if not filtro:
        return

    original = gerar_pautas.ordenar_produtos_para_tentativa
    filtro_cf = filtro.casefold()
    tokens_filtro = _tokens_busca(filtro)

    def ordenar_produtos_priorizando_teste(produtos):
        ordenados = original(produtos)

        encontrados = [
            produto
            for produto in ordenados
            if filtro_cf in str(produto.get("nome", "")).casefold()
        ]

        if not encontrados and tokens_filtro:
            pontuados = []
            for produto in ordenados:
                tokens_nome = _tokens_busca(produto.get("nome", ""))
                comuns = tokens_filtro.intersection(tokens_nome)
                proporcao = len(comuns) / len(tokens_filtro)
                pontuados.append((proporcao, len(comuns), produto))

            pontuados.sort(key=lambda item: (item[0], item[1]), reverse=True)
            melhor_proporcao, melhor_comuns, melhor_produto = pontuados[0]

            if melhor_comuns >= 1 and melhor_proporcao >= 0.50:
                encontrados = [melhor_produto]

        if not encontrados:
            raise RuntimeError(
                "Produto de teste não encontrado no catálogo para o filtro: "
                f"{filtro}"
            )

        nomes_encontrados = {
            str(produto.get("nome", ""))
            for produto in encontrados
        }
        restantes = [
            produto
            for produto in ordenados
            if str(produto.get("nome", "")) not in nomes_encontrados
        ]

        print(
            "\nProduto de teste priorizado:",
            encontrados[0].get("nome", ""),
        )

        return encontrados + restantes

    gerar_pautas.ordenar_produtos_para_tentativa = (
        ordenar_produtos_priorizando_teste
    )


instalar_priorizacao_produto_teste()


def url_interna_wordpress_valida(url):
    url = str(url or "").strip()
    return bool(URL_WORDPRESS) and url.startswith(URL_WORDPRESS)


links_internos.url_interna_valida = url_interna_wordpress_valida


def carregar_lista(caminho):
    if not caminho.exists():
        return []

    try:
        with caminho.open("r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
    except (OSError, json.JSONDecodeError):
        return []

    return dados if isinstance(dados, list) else []


def salvar_lista(caminho, dados):
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open("w", encoding="utf-8") as arquivo:
        json.dump(
            dados,
            arquivo,
            ensure_ascii=False,
            indent=2,
        )
        arquivo.write("\n")


def registrar_rascunho(resultado, pacote):
    rascunhos = carregar_lista(RASCUNHOS_WORDPRESS)

    post_id = resultado.get("id")

    if post_id and any(
        item.get("post_id") == post_id
        for item in rascunhos
        if isinstance(item, dict)
    ):
        return

    pauta = pacote.get("pauta") or {}
    seo = pacote.get("seo") or {}
    artigo = pacote.get("artigo") or {}
    produto = artigo.get("produto_principal") or {}

    rascunhos.append(
        {
            "post_id": post_id,
            "titulo": seo.get("titulo") or pauta.get("titulo"),
            "url": resultado.get("url"),
            "status": resultado.get("status", "draft"),
            "palavra_chave": pauta.get("palavra_chave", ""),
            "categoria": pauta.get("categoria", ""),
            "categoria_wordpress": resultado.get("categoria_slug", ""),
            "produto_principal": produto.get("nome", ""),
            "link_afiliado": produto.get("link_afiliado", ""),
        }
    )

    salvar_lista(
        RASCUNHOS_WORDPRESS,
        rascunhos,
    )


def gerar_pacote_aprovado_wordpress():
    """Gera até três pacotes; só retorna um que passe a segunda trava."""
    max_tentativas_pacote = 3

    for tentativa in range(1, max_tentativas_pacote + 1):
        print(
            f"\n=== VALIDAÇÃO WORDPRESS — PACOTE {tentativa}/"
            f"{max_tentativas_pacote} ==="
        )

        pacote = motor.executar()

        if not isinstance(pacote, dict):
            print("Motor editorial não retornou pacote válido.")
            continue

        artigo = pacote.get("artigo") or {}
        seo = pacote.get("seo") or {}

        if not artigo.get("conteudo_html") or not seo.get("titulo"):
            print("Pacote sem artigo aprovado para o WordPress.")
            continue

        validacao_extra = validar_pacote_wordpress(pacote)

        if validacao_extra["aprovado"]:
            print(
                "Segunda trava editorial do Radar Tech BR: APROVADA."
            )
            pacote["validacao_wordpress"] = validacao_extra
            return pacote

        print(
            "Segunda trava editorial do Radar Tech BR: REPROVADA."
        )

        for problema in validacao_extra["problemas"]:
            print(
                "-",
                problema.get("tipo", "Risco editorial"),
                "|",
                problema.get("trecho", ""),
            )

        print(
            "O pacote foi descartado antes de qualquer envio ao WordPress."
        )

    raise RuntimeError(
        "Nenhum dos pacotes gerados passou pela segunda trava editorial "
        "do Radar Tech BR. Nada foi enviado ao WordPress."
    )


def executar():
    print("=== RADAR TECH BR — WORDPRESS / MODO SEGURO ===")
    print("Destino: WordPress")
    print("Status de saída: RASCUNHO")
    print("Publicação automática no WordPress: DESATIVADA")
    print("Segunda trava editorial WordPress: ATIVA")
    print("Produtos complementares WordPress: DESATIVADOS ATÉ FILTRO POR CATEGORIA")

    filtro_teste = os.getenv("RADARTECH_TEST_PRODUCT_KEYWORD", "").strip()
    if filtro_teste:
        print("Filtro de produto para este teste:", filtro_teste)

    print()

    pacote = gerar_pacote_aprovado_wordpress()

    print("\n=== ENVIO SEGURO AO WORDPRESS ===")
    resultado = criar_post_rascunho(pacote)

    registrar_rascunho(
        resultado,
        pacote,
    )

    print("Rascunho criado com sucesso no Radar Tech BR.")
    print("Título:", resultado.get("titulo"))
    print("Post ID:", resultado.get("id"))
    print("Status:", resultado.get("status"))
    print("Categoria:", resultado.get("categoria_slug"))
    print("Imagem destacada ID:", resultado.get("featured_media") or "sem imagem")
    print("URL:", resultado.get("url"))

    return {
        "pacote": pacote,
        "wordpress": resultado,
    }


if __name__ == "__main__":
    executar()
