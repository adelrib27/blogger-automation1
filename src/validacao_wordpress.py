import re
import unicodedata


REGRAS_EXTRAS_PROMPT = """

REGRAS EXTRAS DE CONFIABILIDADE — RADAR TECH BR:
- Não forneça tempos exatos, faixas de tempo ou estimativas para freezer,
  geladeira, resfriamento, congelamento, aquecimento, cozimento ou conservação
  de alimentos e bebidas quando esses dados não forem fornecidos por uma fonte.
- Não use expressões como "alguns minutos", "algumas horas" ou equivalentes
  para orientar tempo de resfriamento, congelamento, aquecimento ou conservação.
- Não recomende reaproveitar água de gelo derretido para consumo, bebidas,
  drinks ou preparo de alimentos sem informação explícita de potabilidade.
- Não compare vidro, aço inox, plástico, alumínio, tecidos ou outros materiais
  por retenção de temperatura, isolamento, absorção, secagem, resistência,
  durabilidade ou desempenho sem uma base fornecida.
- Em temas de alimentos e bebidas, prefira organização, apresentação,
  planejamento e critérios gerais de escolha. Evite instruções técnicas de
  temperatura, conservação e segurança alimentar.
- Se uma afirmação depender de fabricante, rótulo, embalagem ou manual,
  diga para conferir essa fonte específica em vez de inventar um número.
"""


def _normalizar(texto):
    texto = str(texto or "").lower().strip()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(
        caractere
        for caractere in texto
        if unicodedata.category(caractere) != "Mn"
    )
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()


def _texto_sem_html(conteudo):
    texto = re.sub(r"<[^>]+>", " ", str(conteudo or ""))
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()


def _sentencas(texto):
    return [
        trecho.strip()
        for trecho in re.split(r"(?<=[.!?])\s+", texto or "")
        if trecho.strip()
    ]


def instalar_regras_prompt_wordpress(gerar_artigo_module):
    """Acrescenta regras conservadoras somente ao pipeline WordPress."""
    if getattr(
        gerar_artigo_module,
        "_radartech_prompt_seguro_instalado",
        False,
    ):
        return

    original = gerar_artigo_module.criar_prompt_artigo

    def criar_prompt_artigo_wordpress(*args, **kwargs):
        prompt = original(*args, **kwargs)
        return prompt + REGRAS_EXTRAS_PROMPT

    gerar_artigo_module.criar_prompt_artigo = criar_prompt_artigo_wordpress
    gerar_artigo_module._radartech_prompt_seguro_instalado = True


def validar_conteudo_wordpress(conteudo_html):
    """Segunda trava, específica do Radar Tech BR, antes do REST WordPress."""
    texto = _texto_sem_html(conteudo_html)
    problemas = []
    vistos = set()

    def registrar(tipo, trecho):
        trecho = str(trecho or "").strip()
        chave = (tipo, _normalizar(trecho))
        if trecho and chave not in vistos:
            vistos.add(chave)
            problemas.append(
                {
                    "tipo": tipo,
                    "trecho": trecho[:360],
                }
            )

    padrao_tempo_numerico = re.compile(
        r"\b(?:\d+(?:[.,]\d+)?(?:\s*(?:a|ate|–|-)\s*\d+(?:[.,]\d+)?)?)\s*"
        r"(?:minuto|minutos|hora|horas|dia|dias|semana|semanas|mes|meses)\b"
    )
    padrao_tempo_vago = re.compile(
        r"\b(?:alguns|algumas|poucos|poucas|varios|varias|meia|uma|duas|tres)\s+"
        r"(?:minuto|minutos|hora|horas|dia|dias|semana|semanas)\b"
    )

    verbos_instrucao = (
        "coloque", "colocar", "deixe", "deixar", "mantenha", "manter",
        "resfrie", "resfriar", "congele", "congelar", "aqueça", "aquecer",
        "cozinhe", "cozinhar", "armazene", "armazenar", "guarde", "guardar",
    )
    contextos_termicos = (
        "freezer", "congelador", "geladeira", "refrigerador", "gelo",
        "bebida", "bebidas", "alimento", "alimentos", "comida",
        "resfriamento", "resfriar", "congelamento", "congelar",
        "temperatura", "aquecer", "aquecimento", "cozinhar", "cozimento",
    )
    fontes_especificas = (
        "fabricante", "manual", "rotulo", "embalagem", "etiqueta",
        "instrucoes do produto", "orientacoes do produto",
    )

    materiais = (
        "vidro", "aco inox", "inox", "plastico", "aluminio", "madeira",
        "algodao", "microfibra", "poliester", "silicone", "ceramica",
    )
    efeitos_materiais = (
        "reter o frio", "retem o frio", "reter calor", "retem calor",
        "manter a temperatura", "mantem a temperatura", "isolamento",
        "isolante", "aquecer mais rapido", "aquece mais rapido",
        "esfriar mais rapido", "esfria mais rapido", "absorver mais",
        "absorve mais", "secar mais rapido", "seca mais rapido",
        "mais resistente", "mais duravel", "durabilidade maior",
    )
    linguagem_qualificada = (
        "pode variar", "podem variar", "depende do modelo",
        "dependendo do modelo", "conforme o fabricante",
        "segundo o fabricante", "de acordo com o fabricante",
    )

    for sentenca in _sentencas(texto):
        normalizada = _normalizar(sentenca)

        tem_tempo = bool(
            padrao_tempo_numerico.search(normalizada)
            or padrao_tempo_vago.search(normalizada)
        )
        tem_instrucao = any(v in normalizada for v in verbos_instrucao)
        tem_contexto_termico = any(t in normalizada for t in contextos_termicos)
        tem_fonte = any(t in normalizada for t in fontes_especificas)

        if tem_tempo and tem_instrucao and tem_contexto_termico and not tem_fonte:
            registrar(
                "Tempo técnico de temperatura/conservação sem fonte específica",
                sentenca,
            )

        tem_material = any(t in normalizada for t in materiais)
        tem_efeito_material = any(t in normalizada for t in efeitos_materiais)
        qualificada = any(t in normalizada for t in linguagem_qualificada)

        if tem_material and tem_efeito_material and not qualificada:
            registrar(
                "Comparação de desempenho de material sem base fornecida",
                sentenca,
            )

        agua_gelo = any(
            t in normalizada
            for t in (
                "agua do gelo", "agua que derrete do gelo",
                "agua do gelo derretido", "agua derretida do gelo",
            )
        )
        consumo = any(
            t in normalizada
            for t in (
                "beber", "consumir", "encher os copos", "encher copos",
                "bebida", "bebidas", "drink", "drinks", "coquetel",
                "coqueteis", "preparo de alimentos", "preparar alimentos",
            )
        )
        potabilidade = any(
            t in normalizada
            for t in (
                "agua potavel", "gelo feito com agua potavel",
                "potabilidade confirmada",
            )
        )

        if agua_gelo and consumo and not potabilidade:
            registrar(
                "Recomendação de consumo de água de gelo sem potabilidade explícita",
                sentenca,
            )

    return {
        "aprovado": len(problemas) == 0,
        "problemas": problemas,
        "quantidade_problemas": len(problemas),
    }


def validar_pacote_wordpress(pacote):
    artigo = (pacote or {}).get("artigo") or {}
    return validar_conteudo_wordpress(
        artigo.get("conteudo_html", "")
    )
