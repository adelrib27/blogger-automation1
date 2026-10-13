import re
import unicodedata


REGRAS_EXTRAS_PROMPT = """

REGRAS EXTRAS DE CONFIABILIDADE — RADAR TECH BR:
- Este conteúdo é para o site Radar Tech BR. Adapte o texto ao tema real da
  pauta, que pode ser tecnologia, casa, cozinha, moda, beleza, ferramentas
  ou automotivo. Não force exemplos de Casa e Decoração quando não couberem.
- Não forneça tempos exatos, faixas de tempo ou estimativas para freezer,
  geladeira, resfriamento, congelamento, aquecimento, cozimento ou conservação
  de alimentos e bebidas quando esses dados não forem fornecidos por uma fonte.
- Não use expressões como "alguns minutos", "algumas horas" ou equivalentes
  para orientar tempo de resfriamento, congelamento, aquecimento ou conservação.
- Não recomende reaproveitar água de gelo derretido para consumo, bebidas,
  drinks ou preparo de alimentos sem informação explícita de potabilidade.
- Não compare vidro, aço inox, plástico, alumínio, tecidos, superfícies ou
  outros materiais por retenção de temperatura, aderência, atrito, deslizamento,
  isolamento, absorção, secagem, resistência, durabilidade ou desempenho sem
  uma base fornecida.
- Não afirme que um tipo de tecido ou superfície "adere melhor", "escorrega
  menos", "fica mais firme", "aumenta a fricção" ou equivalentes sem fonte.
- Não recomende cortar, perfurar, colar, amarrar ou adicionar pesos a um item
  como solução improvisada, a menos que isso esteja previsto pelo fabricante.
- Em tecnologia, não invente alcance, autonomia, potência, latência,
  compatibilidade, proteção contra água, certificação, velocidade, resolução,
  capacidade, frequência ou qualquer especificação técnica.
- Em beleza e cuidados pessoais, não prometa reduzir frizz, evitar danos,
  fortalecer, hidratar, estimular crescimento, proteger fios/pele ou produzir
  resultado fisiológico sem base explícita.
- Em temas de alimentos e bebidas, prefira organização, apresentação,
  planejamento e critérios gerais de escolha. Evite instruções técnicas de
  temperatura, conservação e segurança alimentar.
- Se uma afirmação depender de fabricante, rótulo, embalagem ou manual,
  diga para conferir essa fonte específica em vez de inventar um número.
"""


REGRAS_EXTRAS_PAUTA = """

REGRAS ESPECÍFICAS DO RADAR TECH BR — SUBSTITUEM A LISTA DE CATEGORIAS
LEGADA QUANDO HOUVER CONFLITO:
- O site é Radar Tech BR e cobre múltiplas categorias.
- Use somente uma destas categorias editoriais:
  Tecnologia
  Casa & Decoração
  Cozinha & Utilidades
  Moda & Beleza
  Ferramentas & Automotivo
  Guias de Compra
- A categoria deve acompanhar o produto real. Não classifique tecnologia,
  beleza ou automotivo como Casa/Quarto/Cozinha apenas por causa das regras
  legadas do motor.
- Evite pautas baseadas em benefício técnico não comprovado pelo nome do
  produto. Prefira critérios de escolha, situações de uso, organização,
  comparação de formatos e dúvidas de compra que não exijam inventar dados.
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
        prompt = prompt.replace(
            'blog "Achados para Casa"',
            'site "Radar Tech BR"',
        )
        prompt = prompt.replace(
            "Casa, Organização e Decoração",
            "guias de compra, tecnologia, casa, cozinha, moda, beleza, ferramentas e automotivo",
        )
        return prompt + REGRAS_EXTRAS_PROMPT

    gerar_artigo_module.criar_prompt_artigo = criar_prompt_artigo_wordpress
    gerar_artigo_module._radartech_prompt_seguro_instalado = True


def instalar_regras_pauta_wordpress(gerar_pautas_module):
    """Adapta a geração de pautas ao escopo multitemático do Radar Tech BR."""
    if getattr(
        gerar_pautas_module,
        "_radartech_pauta_segura_instalada",
        False,
    ):
        return

    original = gerar_pautas_module.criar_prompt_produto

    def criar_prompt_produto_wordpress(*args, **kwargs):
        prompt = original(*args, **kwargs)
        return prompt + REGRAS_EXTRAS_PAUTA

    gerar_pautas_module.criar_prompt_produto = criar_prompt_produto_wordpress
    gerar_pautas_module._radartech_pauta_segura_instalada = True


def _remover_texto_comercial(conteudo_html, produto_principal=""):
    """Retira do texto analisado os trechos comerciais inseridos pelo Python."""
    texto = _texto_sem_html(conteudo_html)

    if produto_principal:
        texto = re.sub(
            re.escape(str(produto_principal)),
            " ",
            texto,
            flags=re.IGNORECASE,
        )

    expressoes = (
        "PRODUTO RELACIONADO AO TEMA",
        "VER PRODUTO E CONFERIR A OFERTA",
        "VER PRODUTO",
        "Uma opção relacionada ao conteúdo que você acabou de ler.",
        "Veja os detalhes do produto diretamente no anúncio.",
        "Preço, disponibilidade, características e condições podem variar conforme o modelo e o anúncio do vendedor.",
        "Confira os detalhes na página do produto antes da compra.",
        "Transparência: este é um link de afiliado.",
        "Se você comprar por meio dele, podemos receber uma comissão, sem custo adicional para você.",
    )

    for expressao in expressoes:
        texto = texto.replace(expressao, " ")

    return re.sub(r"\s+", " ", texto).strip()


def validar_conteudo_wordpress(conteudo_html, produto_principal=""):
    """Segunda trava, específica do Radar Tech BR, antes do REST WordPress."""
    texto = _remover_texto_comercial(
        conteudo_html,
        produto_principal=produto_principal,
    )
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
        "resfrie", "resfriar", "congele", "congelar", "aqueca", "aquecer",
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
        "instrucoes do produto", "orientacoes do produto", "ficha tecnica",
        "especificacoes oficiais", "pagina oficial",
    )

    contextos_materiais = (
        "vidro", "aco inox", "inox", "plastico", "aluminio", "madeira",
        "algodao", "microfibra", "poliester", "silicone", "ceramica",
        "linho", "tecido", "tecidos", "fibra", "fibras", "superficie",
        "superficies", "borracha", "feltro",
    )
    efeitos_materiais = (
        "reter o frio", "retem o frio", "reter calor", "retem calor",
        "manter a temperatura", "mantem a temperatura", "isolamento",
        "isolante", "aquecer mais rapido", "aquece mais rapido",
        "esfriar mais rapido", "esfria mais rapido", "absorver mais",
        "absorve mais", "secar mais rapido", "seca mais rapido",
        "mais resistente", "mais duravel", "durabilidade maior",
        "aderencia", "aderir", "adere", "fixacao", "fixar", "se fixar",
        "friccao", "atrito", "deslizamento", "deslizar", "escorregar",
        "escorrega", "estabilidade", "mais firme", "maior densidade",
        "respiravel", "respirabilidade", "temperatura corporal",
        "mais eficaz", "mais eficiente", "ajuda a manter o tecido",
        "ajuda a manter a toalha", "reduzir o deslizamento",
        "reduz o deslizamento", "melhor fixacao",
    )

    padrao_especificacao_tecnica = re.compile(
        r"\b\d+(?:[.,]\d+)?\s*(?:w|kw|v|mah|ah|hz|khz|mhz|ghz|db|"
        r"km/h|km|cm|mm|mp|gb|tb|fps|rpm|canais?)\b|"
        r"\b(?:ipx\d+|ip\d{2})\b|\b\d+(?:[.,]\d+)?\s*(?:°c|celsius)\b"
    )
    contextos_tecnologia = (
        "headset", "fone", "bluetooth", "camera", "celular", "computador",
        "usb", "microfone", "radio", "scanner", "obd", "caixa de som",
        "bateria", "carregamento", "motor", "led", "rgb", "wifi", "wi fi",
        "aparelho", "dispositivo", "equipamento", "eletronico", "eletronica",
    )

    contextos_beleza = (
        "cabelo", "cabelos", "fio", "fios", "barba", "pele", "couro cabeludo",
        "chapinha", "prancha", "barbeador", "shaver", "maquina de cortar cabelo",
    )
    alegacoes_beleza = (
        "reduz frizz", "reduzir frizz", "evita danos", "evitar danos",
        "protege os fios", "proteger os fios", "protege a pele", "proteger a pele",
        "fortalece", "fortalecer", "estimula o crescimento", "estimular o crescimento",
        "hidrata", "hidratar", "nutre", "nutrir", "sela cuticulas",
        "selar cuticulas", "nao danifica", "menos agressivo", "mais saudavel",
        "evita irritacao", "reduz irritacao", "sem irritar",
    )

    modificacoes_improvisadas = (
        "cortar a toalha", "cortar o tecido", "perfurar", "fazer furos",
        "colar na", "colar o", "usar adesivo", "adicionar peso",
        "adicionar pesos", "usar pesos", "peso nas bordas", "pesos nas bordas",
        "amarrar", "usar amarras", "usar cordoes", "cordoes nos cantos",
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

        tem_material = any(t in normalizada for t in contextos_materiais)
        tem_efeito_material = any(t in normalizada for t in efeitos_materiais)

        if tem_material and tem_efeito_material and not tem_fonte:
            registrar(
                "Propriedade ou desempenho de material/superfície sem base fornecida",
                sentenca,
            )

        if (
            any(t in normalizada for t in modificacoes_improvisadas)
            and not tem_fonte
        ):
            registrar(
                "Modificação física improvisada sem orientação do fabricante",
                sentenca,
            )

        tem_tecnologia = any(t in normalizada for t in contextos_tecnologia)
        tem_especificacao = bool(padrao_especificacao_tecnica.search(normalizada))

        if tem_tecnologia and tem_especificacao and not tem_fonte:
            registrar(
                "Especificação técnica numérica sem fonte oficial",
                sentenca,
            )

        if (
            tem_tecnologia
            and any(
                termo in normalizada
                for termo in (
                    "compativel com", "compatibilidade com", "funciona com",
                    "serve para", "alcance de", "autonomia de", "latencia de",
                    "a prova d agua", "resistente a agua", "cancelamento de ruido",
                )
            )
            and not tem_fonte
        ):
            registrar(
                "Compatibilidade ou capacidade técnica sem fonte oficial",
                sentenca,
            )

        if (
            any(t in normalizada for t in contextos_beleza)
            and any(t in normalizada for t in alegacoes_beleza)
            and not tem_fonte
        ):
            registrar(
                "Benefício de beleza/cuidados pessoais sem base fornecida",
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
    produto = artigo.get("produto_principal") or {}
    nome_produto = produto.get("nome", "") if isinstance(produto, dict) else ""

    return validar_conteudo_wordpress(
        artigo.get("conteudo_html", ""),
        produto_principal=nome_produto,
    )
