import json
import re
import unicodedata
from pathlib import Path

import gerar_artigo
import gerar_pautas
import main as motor
import wordpress_api


BASE_DIR = Path(__file__).resolve().parent.parent
CURRENT_PRODUCT_PATH = BASE_DIR / "data" / "fase3" / "produto_atual.json"

CATEGORY_SLUGS = {
    "Tecnologia": "tecnologia",
    "Casa & Decoração": "casa-decoracao",
    "Cozinha & Utilidades": "cozinha-utilidades",
    "Ferramentas & Automotivo": "ferramentas-automotivo",
    "Moda & Beleza": "moda-beleza",
}

GENERIC_KEYWORD_TOKENS = {
    "produto",
    "produtos",
    "organizador",
    "organizadores",
    "portatil",
    "portateis",
}

TITLE_WEAK_ENDINGS = {
    "a",
    "as",
    "com",
    "como",
    "da",
    "das",
    "de",
    "do",
    "dos",
    "e",
    "em",
    "na",
    "nas",
    "no",
    "nos",
    "o",
    "os",
    "ou",
    "para",
    "pela",
    "pelas",
    "pelo",
    "pelos",
    "por",
    "sem",
    "um",
    "uma",
}


def _load_current():
    try:
        data = json.loads(CURRENT_PRODUCT_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _normalize(text):
    value = unicodedata.normalize("NFKD", str(text or "").casefold())
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def _keyword_tokens(keyword):
    tokens = {
        token
        for token in _normalize(keyword).split()
        if len(token) >= 3 and token not in GENERIC_KEYWORD_TOKENS
    }
    if tokens:
        return tokens
    return {
        token
        for token in _normalize(keyword).split()
        if len(token) >= 3
    }


def _ajustar_titulo_natural(titulo, limite=60):
    """Encurta títulos sem deixá-los terminando em conectivos ou frases penduradas."""
    original = re.sub(r"\s+", " ", str(titulo or "")).strip()
    if not original:
        return ""

    candidato = original
    if len(candidato) > limite:
        candidato = candidato[:limite].rstrip()
        if " " in candidato:
            candidato = candidato.rsplit(" ", 1)[0].rstrip()

    palavras = candidato.split()

    while len(palavras) > 3:
        normalizadas = [_normalize(palavra) for palavra in palavras]

        # Evita cortes como "... de forma" quando o complemento ficou fora do limite.
        if len(normalizadas) >= 2 and normalizadas[-2:] == ["de", "forma"]:
            palavras = palavras[:-2]
            continue

        if normalizadas[-1] in TITLE_WEAK_ENDINGS:
            palavras = palavras[:-1]
            continue

        break

    ajustado = " ".join(palavras).rstrip(" ,.;:-")
    return ajustado or candidato.rstrip(" ,.;:-")


def instalar():
    current = _load_current()
    category = str(current.get("category") or "").strip()
    keyword = str(current.get("keyword") or "").strip()

    if category not in CATEGORY_SLUGS or not keyword:
        raise RuntimeError(
            "Contexto da fila Fase 3 incompleto para instalar a trava semântica."
        )

    # A categoria definida pela fila é a autoridade final também no REST WordPress.
    original_category_mapper = wordpress_api.mapear_categoria_slug

    def mapear_categoria_fase3(categoria="", titulo="", produto=""):
        normalized_category = _normalize(categoria)
        for display_name, slug in CATEGORY_SLUGS.items():
            if normalized_category == _normalize(display_name):
                return slug
        return original_category_mapper(
            categoria=categoria,
            titulo=titulo,
            produto=produto,
        )

    wordpress_api.mapear_categoria_slug = mapear_categoria_fase3

    # Faz a pauta nascer da intenção que qualificou o produto na fila.
    original_prompt = gerar_pautas.criar_prompt_produto

    def criar_prompt_fase3(*args, **kwargs):
        prompt = original_prompt(*args, **kwargs)
        return (
            prompt
            + f"""

CONTEXTO OBRIGATÓRIO DA FILA — RADAR TECH BR FASE 3:
- Categoria editorial obrigatória: {category}
- Termo/intenção que qualificou o produto: {keyword}
- Todas as pautas devem permanecer diretamente ligadas a essa intenção de busca.
- O título, a palavra-chave principal e a descrição devem refletir naturalmente essa intenção.
- Se o produto tiver usos em várias áreas, NÃO troque para outro ambiente ou categoria só porque outro termo também aparece no nome do anúncio.
- Prefira o ângulo correspondente a "{keyword}".
- Retorne exatamente "{category}" no campo categoria.
"""
        )

    gerar_pautas.criar_prompt_produto = criar_prompt_fase3

    # Mantém dicas editoriais úteis sem transformar conhecimento geral em
    # característica, instrução ou garantia específica do produto selecionado.
    original_article_prompt = gerar_artigo.criar_prompt_artigo

    def criar_prompt_artigo_fase3(*args, **kwargs):
        prompt = original_article_prompt(*args, **kwargs)
        return (
            prompt
            + """

CALIBRAÇÃO DE ORIENTAÇÕES GERAIS — FASE 3:
- Dicas gerais de organização, comparação, conservação e boas práticas são permitidas quando forem claramente apresentadas como orientação editorial geral.
- Não apresente uma orientação geral como se fosse característica, instrução oficial ou capacidade confirmada do produto específico.
- Limpeza, manutenção, compatibilidade, segurança, instalação, materiais, medidas, desempenho e garantia específicos do produto só podem ser afirmados quando houver dado de origem que sustente a afirmação.
- Quando um procedimento específico não estiver confirmado, prefira orientar o leitor a conferir o anúncio, a ficha técnica ou o manual do modelo.
- O objetivo é manter o artigo útil e natural, sem preencher lacunas do produto por inferência.
"""
        )

    gerar_artigo.criar_prompt_artigo = criar_prompt_artigo_fase3

    # Evita títulos SEO cortados no meio da ideia. O ajuste ocorre antes da
    # função SEO original, preservando slug e demais campos coerentes com o título.
    original_preparar_seo = motor.preparar_seo

    def preparar_seo_fase3(*args, **kwargs):
        argumentos = list(args)
        limite = int(kwargs.get("titulo_max", 60) or 60)

        if "titulo" in kwargs:
            kwargs["titulo"] = _ajustar_titulo_natural(kwargs.get("titulo"), limite)
        elif argumentos:
            argumentos[0] = _ajustar_titulo_natural(argumentos[0], limite)

        return original_preparar_seo(*argumentos, **kwargs)

    motor.preparar_seo = preparar_seo_fase3

    # Entre as candidatas válidas, prioriza as que preservam os termos distintivos
    # da keyword da fila antes do anti-repetição escolher a primeira inédita.
    original_selector = gerar_pautas.selecionar_pauta_inedita
    target_tokens = _keyword_tokens(keyword)

    def selecionar_pauta_fase3(pautas, produto_principal):
        def score(pauta):
            if not isinstance(pauta, dict):
                return -1
            text = _normalize(
                " ".join(
                    [
                        str(pauta.get("titulo") or ""),
                        str(pauta.get("palavra_chave") or ""),
                        str(pauta.get("descricao") or ""),
                    ]
                )
            )
            found = sum(1 for token in target_tokens if token in text.split())
            phrase_bonus = 2 if _normalize(keyword) in text else 0
            return found * 10 + phrase_bonus

        ordered = sorted(
            list(pautas or []),
            key=score,
            reverse=True,
        )
        return original_selector(ordered, produto_principal)

    gerar_pautas.selecionar_pauta_inedita = selecionar_pauta_fase3

    print(
        "Trava Fase 3 instalada:",
        f"categoria={category} | keyword={keyword}",
    )
