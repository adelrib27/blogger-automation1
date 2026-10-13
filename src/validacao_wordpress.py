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
- Em tecnologia, trate recursos como critérios a conferir no anúncio/manual;
  não diga que um recurso genérico reduz fadiga, melhora imersão, aumenta
  desempenho, facilita precisão ou produz outro resultado sem base fornecida.
- Em Moda & Beleza, quando o tema envolver máquina de cortar cabelo, barbeador,
  shaver, chapinha ou prancha, escreva como GUIA DE COMPRA, não como tutorial
  técnico de corte, barbear ou tratamento dos fios.
- Em aparelhos de beleza, não ensine técnica de corte em camadas, fade, posição
  de lâmina, ângulo de corte, uso em cabelo molhado/seco ou procedimento de
  barbear. Oriente a seguir o manual e, quando necessário, um profissional.
- Não atribua a potência do motor, material/revestimento da lâmina, peso,
  ergonomia, ruído, autonomia ou carregamento qualquer vantagem de corte,
  durabilidade, precisão, conforto, irritação ou desempenho sem fonte.
- Não recomende lubrificação, frequência de limpeza, armazenamento, exposição
  à umidade/temperatura ou cuidado de bateria como regra geral. Diga para
  seguir o manual específico do aparelho.
- Em beleza e cuidados pessoais, não prometa reduzir frizz, evitar danos,
  fortalecer, hidratar, estimular crescimento, proteger fios/pele ou produzir
  resultado fisiológico sem base explícita.
- Não recomende óleos, máscaras caseiras, shampoo, condicionador ou outros
  tratamentos como forma de preservar corte, hidratar ou melhorar a saúde dos
  fios sem uma fonte adequada.
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
- Em títulos de Moda & Beleza, não acrescente promessa de resultado a um
  recurso. Evite construções como "visor LCD para cortes precisos", "motor
  potente para cortar sem esforço", "chapinha para não danificar os fios"
  ou equivalentes quando esse benefício não estiver comprovado.
- Para máquinas de cortar cabelo, barbeadores, shavers, chapinhas e pranchas,
  prefira pautas de escolha e comparação de critérios; não gere tutoriais de
  técnica de corte, barbear ou tratamento capilar.
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


def _produto_eh_aparelho_beleza(produto_principal, categoria="", titulo=""):
    base = _normalizar(
        " ".join(
            [
                str(produto_principal or ""),
                str(categoria or ""),
                str(titulo or ""),
            ]
        )
    )
    termos = (
        "maquina de cortar cabelo",
        "maquina de acabamento",
        "barbeador",
        "shaver",
        "chapinha",
        "prancha de cabelo",
        "aparador de pelos",
        "moda & beleza",
        "moda e beleza",
    )
    return any(termo in base for termo in termos)


def validar_conteudo_wordpress(
    conteudo_html,
    produto_principal="",
    titulo="",
    categoria="",
):
    """Segunda trava, específica do Radar Tech BR, antes do REST WordPress."""
    texto = _remover_texto_comercial(
        conteudo_html,
        produto_principal=produto_principal,
    )
    problemas = []
    vistos = set()
    aparelho_beleza = _produto_eh_aparelho_beleza(
        produto_principal,
        categoria=categoria,
        titulo=titulo,
    )

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
        "especificacoes oficiais", "pagina oficial", "anuncio do vendedor",
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
        "visual mais saudavel", "evita irritacao", "reduz irritacao", "sem irritar",
        "preservar a forma", "preservar o corte", "prolongar a vida do corte",
    )

    modificacoes_improvisadas = (
        "cortar a toalha", "cortar o tecido", "perfurar", "fazer furos",
        "colar na", "colar o", "usar adesivo", "adicionar peso",
        "adicionar pesos", "usar pesos", "peso nas bordas", "pesos nas bordas",
        "amarrar", "usar amarras", "usar cordoes", "cordoes nos cantos",
    )

    termos_tecnica_corte = (
        "lâmina paralela", "lamina paralela", "corte em camadas", "tecnica de fade",
        "fade", "angulo de corte", "cortar pequenas porcoes", "corte uma secao",
        "corte os fios", "corte um pouco", "penteado de referencia",
        "cabelo molhado", "cabelo umido", "cabelo seco", "couro cabeludo",
        "tesoura de ponta", "tesoura com", "linha reta ou curva",
    )
    manutencao_aparelho = (
        "limpe as laminas", "limpar as laminas", "limpeza apos cada uso",
        "apos cada uso", "lubrificacao", "lubrificar", "oleo lubrificante",
        "armazene o equipamento", "armazenamento adequado", "local seco",
        "umidade excessiva", "temperaturas extremas", "bateria descarregada",
        "deixa-la descarregada", "substitua as laminas", "substituir as laminas",
        "prolongar a vida util", "preservar o desempenho", "manter a eficiencia",
    )
    desempenho_laminas = (
        "qualidade das laminas", "laminas de boa qualidade", "laminas finas",
        "laminas largas", "laminas robustas", "laminas mais robustas",
        "laminas mais leves", "laminas de aco inoxidavel", "revestimento especial",
        "afiacao", "mais duraveis", "durabilidade", "resistentes a corrosao",
        "reduzir o atrito", "menos atrito", "irritacao", "cortes mais precisos",
        "corte mais preciso", "cortes uniformes", "forca de corte",
    )
    desempenho_motor_bateria = (
        "potencia do motor", "motor potente", "maior potencia", "capacidade de cortar",
        "cabelos densos", "cabelos grossos", "fios grossos", "sem esforco",
        "bateria de longa duracao", "autonomia prolongada", "autonomia superior",
        "carregamento rapido", "recarga rapida", "baterias removiveis",
        "carregamento via usb", "multiplios ciclos", "multiplos ciclos",
    )
    ergonomia_beneficio = (
        "reduzir a fadiga", "reduz a fadiga", "evitar fadiga", "mais confortavel",
        "maior controle", "reduzir a tensao", "reduz a tensao", "menos cansaco",
        "mais manejavel", "maior estabilidade", "peso equilibrado",
        "alcas antiderrapantes", "superficies antiderrapantes", "mais silencioso",
        "mais silenciosos", "vantajoso", "vantajosa",
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

        if aparelho_beleza and not tem_fonte:
            if any(t in normalizada for t in termos_tecnica_corte):
                registrar(
                    "Tutorial técnico de corte/barbear inadequado para guia de compra",
                    sentenca,
                )

            if any(t in normalizada for t in manutencao_aparelho):
                registrar(
                    "Manutenção de aparelho sem orientação do fabricante",
                    sentenca,
                )

            if (
                "lamina" in normalizada
                and any(t in normalizada for t in desempenho_laminas)
            ):
                registrar(
                    "Desempenho de lâmina não sustentado por fonte",
                    sentenca,
                )

            if any(t in normalizada for t in desempenho_motor_bateria):
                registrar(
                    "Desempenho de motor/bateria não sustentado por fonte",
                    sentenca,
                )

            if any(t in normalizada for t in ergonomia_beneficio):
                registrar(
                    "Benefício ergonômico ou de conforto não sustentado",
                    sentenca,
                )

            if (
                any(t in normalizada for t in ("tipo de cabelo", "cabelos finos", "cabelos grossos", "fios finos", "fios grossos", "cabelos crespos", "cabelos ondulados"))
                and any(t in normalizada for t in ("exige", "exigem", "demanda", "demandam", "precisa", "precisam", "indicado", "indicada", "ideal", "adequado", "adequada", "lamina", "potencia"))
            ):
                registrar(
                    "Recomendação técnica por tipo de cabelo sem base fornecida",
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


def validar_titulo_meta_wordpress(
    titulo,
    meta_description,
    produto_principal="",
    categoria="",
):
    """Evita promessa de resultado já no título ou na meta description."""
    problemas = []
    texto = _normalizar(f"{titulo} {meta_description}")

    if _produto_eh_aparelho_beleza(
        produto_principal,
        categoria=categoria,
        titulo=titulo,
    ):
        promessas = (
            "para cortes precisos", "corte preciso", "cortes precisos",
            "sem esforco", "sem danificar", "evitar danos", "reduz frizz",
            "mais conforto", "sem irritacao", "resultado perfeito",
            "resultado profissional", "mais eficiente",
        )
        for promessa in promessas:
            if promessa in texto:
                problemas.append(
                    {
                        "tipo": "Promessa de resultado no título/meta sem base fornecida",
                        "trecho": str(titulo or meta_description)[:360],
                    }
                )
                break

    return {
        "aprovado": len(problemas) == 0,
        "problemas": problemas,
        "quantidade_problemas": len(problemas),
    }


def validar_pacote_wordpress(pacote):
    pacote = pacote or {}
    artigo = pacote.get("artigo") or {}
    pauta = pacote.get("pauta") or {}
    seo = pacote.get("seo") or {}
    produto = artigo.get("produto_principal") or {}
    nome_produto = produto.get("nome", "") if isinstance(produto, dict) else ""
    titulo = seo.get("titulo") or pauta.get("titulo") or artigo.get("titulo") or ""
    meta_description = seo.get("meta_description") or seo.get("descricao") or ""
    categoria = pauta.get("categoria") or artigo.get("categoria") or ""

    validacao_conteudo = validar_conteudo_wordpress(
        artigo.get("conteudo_html", ""),
        produto_principal=nome_produto,
        titulo=titulo,
        categoria=categoria,
    )
    validacao_titulo = validar_titulo_meta_wordpress(
        titulo=titulo,
        meta_description=meta_description,
        produto_principal=nome_produto,
        categoria=categoria,
    )

    problemas = (
        validacao_conteudo.get("problemas", [])
        + validacao_titulo.get("problemas", [])
    )

    return {
        "aprovado": len(problemas) == 0,
        "problemas": problemas,
        "quantidade_problemas": len(problemas),
    }
