import html
import re
import unicodedata


TERMOS_APARELHO_BELEZA = (
    "maquina de cortar cabelo",
    "maquina de acabamento",
    "barbeador",
    "shaver",
    "chapinha",
    "prancha de cabelo",
    "aparador de pelos",
)


def _normalizar(texto):
    texto = str(texto or "").casefold()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(
        caractere
        for caractere in texto
        if unicodedata.category(caractere) != "Mn"
    )
    texto = re.sub(r"[^a-z0-9]+", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()


def _slug(texto):
    texto = _normalizar(texto)
    return re.sub(r"\s+", "-", texto).strip("-")


def produto_requer_modo_fact_safe(produto):
    if not isinstance(produto, dict):
        return False

    nome = _normalizar(produto.get("nome", ""))
    if not any(termo in nome for termo in TERMOS_APARELHO_BELEZA):
        return False

    fatos = produto.get("fatos_confirmados")
    if isinstance(fatos, list) and any(str(item).strip() for item in fatos):
        return False

    return True


def _identidade_produto(nome):
    normalizado = _normalizar(nome)

    if "kemei pg 2600" in normalizado:
        return {
            "titulo": "Kemei PG-2600 com visor LCD: o que conferir antes de comprar",
            "palavra_chave": "Kemei PG-2600 visor LCD",
            "rotulo": "Kemei PG-2600",
        }

    if "maquina de cortar cabelo" in normalizado:
        return {
            "titulo": "Máquina de cortar cabelo: o que conferir antes de comprar",
            "palavra_chave": "máquina de cortar cabelo",
            "rotulo": "máquina de cortar cabelo",
        }

    if "barbeador" in normalizado or "shaver" in normalizado:
        return {
            "titulo": "Barbeador elétrico: o que conferir antes de comprar",
            "palavra_chave": "barbeador elétrico",
            "rotulo": "barbeador elétrico",
        }

    if "chapinha" in normalizado or "prancha de cabelo" in normalizado:
        return {
            "titulo": "Prancha de cabelo: o que conferir antes de comprar",
            "palavra_chave": "prancha de cabelo",
            "rotulo": "prancha de cabelo",
        }

    return {
        "titulo": "Aparelho de beleza: o que conferir antes de comprar",
        "palavra_chave": "aparelho de beleza",
        "rotulo": "aparelho de beleza",
    }


def _fatos_literais(nome):
    normalizado = _normalizar(nome)
    fatos = []

    if "maquina de cortar cabelo" in normalizado:
        fatos.append("O nome do anúncio identifica o item como máquina de cortar cabelo.")

    if "kemei pg 2600" in normalizado:
        fatos.append("O nome do anúncio informa Kemei PG-2600.")

    if "sem fio" in normalizado:
        fatos.append("O nome do anúncio informa que o modelo é sem fio.")

    if "visor lcd" in normalizado:
        fatos.append("O nome do anúncio informa a presença de visor LCD.")

    if not fatos:
        fatos.append(
            "A identificação disponível no catálogo é o próprio nome do anúncio; "
            "os demais detalhes devem ser confirmados na página do produto."
        )

    return fatos


def _lista_html(itens):
    return "\n".join(
        f"<li>{html.escape(str(item))}</li>"
        for item in itens
    )


def _conteudo_fact_safe(nome_produto, bloco_produto):
    nome = html.escape(str(nome_produto))
    fatos = _fatos_literais(nome_produto)

    return f"""
<p>Ao avaliar <strong>{nome}</strong>, o ponto mais importante é separar o que o nome do anúncio realmente confirma do que ainda precisa ser verificado. Este guia adota uma abordagem conservadora: não atribui ao produto autonomia, potência, acessórios, funções do visor, materiais, medidas ou desempenho que não estejam informados no catálogo.</p>

<p>Isso ajuda a comparar ofertas com mais clareza. Em vez de preencher lacunas com características comuns de outros aparelhos, a recomendação é usar a página do produto, a ficha técnica e o manual como fontes para cada detalhe específico.</p>

<h2>O que o nome do anúncio confirma</h2>
<p>Com base apenas na identificação recebida no catálogo, estes são os pontos que podem ser tratados como confirmados:</p>
<ul>
{_lista_html(fatos)}
</ul>
<p>Essas informações são suficientes para identificar o produto, mas não permitem concluir, por exemplo, quais acessórios acompanham a caixa, qual é a faixa de ajuste, como funciona a alimentação, o que aparece no visor ou quais são as condições de garantia.</p>

<h2>O que conferir sobre o visor LCD</h2>
<p>A expressão <strong>visor LCD</strong> confirma a presença do visor, mas não informa por si só qual conteúdo ele apresenta. Antes de comprar, confira na página do produto ou no manual qual informação é exibida e se as fotos do anúncio mostram esse recurso de forma clara.</p>

<p>Se a descrição não explicar a função do visor, vale tratar esse ponto como uma dúvida de compra. A pergunta útil não é “o que esse tipo de visor costuma mostrar?”, mas sim “o que o visor deste modelo específico mostra segundo o anúncio ou o fabricante?”. Essa diferença evita comparar o produto com recursos que podem pertencer a outro modelo.</p>

<h2>O que verificar sobre o funcionamento sem fio</h2>
<p>O termo <strong>sem fio</strong> faz parte do nome do produto. Ainda assim, ele não informa sozinho detalhes de alimentação, recarga, autonomia ou itens necessários para o funcionamento. Esses dados devem ser confirmados na ficha técnica do modelo antes da decisão.</p>

<p>Ao comparar anúncios, procure uma descrição objetiva do sistema de alimentação e das condições indicadas pelo fabricante. Se alguma informação importante estiver ausente, prefira confirmar na própria página do produto ou com o vendedor, sem assumir valores ou características com base em aparelhos parecidos.</p>

{bloco_produto}

<h2>Ajustes e acessórios: confirme o que realmente acompanha</h2>
<p>O nome disponível no catálogo não confirma a quantidade de acessórios, pentes, cabos, bases, estojos ou outros itens. Também não confirma medidas de corte ou faixas de regulagem. Por isso, esses pontos devem ser lidos diretamente na relação de itens inclusos e na ficha técnica do anúncio.</p>

<p>Uma boa comparação entre ofertas do mesmo modelo deve observar se os anúncios descrevem o mesmo conjunto. Quando houver diferenças, use a lista oficial de itens inclusos como referência. Isso é mais seguro do que deduzir o conteúdo da caixa pelas fotos ou pela experiência com produtos semelhantes.</p>

<h2>Como comparar anúncios do mesmo modelo</h2>
<p>Comece pela identificação exata do produto e verifique se o nome do modelo coincide. Depois, compare apenas campos que estejam explicitamente informados em cada anúncio. Se um vendedor detalha uma característica e outro não, a ausência de informação não deve ser interpretada como confirmação nem como negação.</p>

<p>Também vale conferir quem é responsável pela venda, as condições de envio, a política de devolução, a garantia informada e a disponibilidade apresentada no momento da consulta. Esses elementos podem mudar com o tempo e fazem parte da decisão de compra tanto quanto a descrição técnica.</p>

<h2>Manual e ficha técnica são a referência para uso e manutenção</h2>
<p>Para limpeza, conservação, troca de peças, alimentação e qualquer procedimento de manutenção, siga as instruções específicas do fabricante. Este guia não substitui o manual e não recomenda uma rotina genérica, porque aparelhos diferentes podem exigir cuidados diferentes.</p>

<p>Se a página do produto disponibilizar manual, ficha técnica ou documentação do fabricante, use esses materiais para confirmar os pontos que não aparecem no título. Quando não houver documentação acessível, registre a dúvida antes da compra em vez de completar a informação por suposição.</p>

<h2>Checklist final antes da compra</h2>
<p>Antes de decidir, confira se o anúncio responde de forma clara às perguntas abaixo:</p>
<ul>
<li>O modelo informado corresponde exatamente ao produto que você pretende comprar?</li>
<li>A página explica o que o visor LCD deste modelo apresenta?</li>
<li>O anúncio detalha como funciona a alimentação do modelo sem fio?</li>
<li>Os itens inclusos estão listados de forma objetiva?</li>
<li>As opções de ajuste e as medidas, se houver, estão descritas na ficha técnica?</li>
<li>Há orientação do fabricante ou manual disponível para consulta?</li>
<li>Garantia, devolução, envio, disponibilidade e condições da oferta estão claros no momento da compra?</li>
</ul>

<p>Para o <strong>{nome}</strong>, a estratégia mais segura é simples: considerar como fato apenas o que está explicitamente informado e transformar o restante em itens de verificação. Assim, o artigo continua útil para a decisão de compra sem atribuir ao produto características que ainda não foram confirmadas.</p>
""".strip()


def criar_pacote_fact_safe(produto, motor, validar_pacote_wordpress):
    if not isinstance(produto, dict):
        raise RuntimeError("Produto inválido para o modo fact-safe.")

    nome = str(produto.get("nome", "")).strip()
    link = str(produto.get("link_afiliado", "")).strip()

    if not nome or not link:
        raise RuntimeError("Produto fact-safe sem nome ou link afiliado.")

    identidade = _identidade_produto(nome)
    titulo = identidade["titulo"]
    palavra_chave = identidade["palavra_chave"]
    descricao = (
        f"Checklist do {identidade['rotulo']}: veja o que o anúncio confirma "
        "e quais detalhes conferir na ficha técnica antes da compra."
    )
    descricao = descricao[:155].rstrip()

    produto_principal = motor.preparar_produto_principal(
        {
            "nome": nome,
            "link_afiliado": link,
        }
    )
    produto_principal = motor.enriquecer_produto_com_imagem(produto_principal)

    bloco_produto = motor.criar_bloco_produto_principal(produto_principal)
    conteudo_html = _conteudo_fact_safe(
        nome_produto=nome,
        bloco_produto=bloco_produto,
    )

    pauta = {
        "titulo": titulo,
        "palavra_chave": palavra_chave,
        "descricao": descricao,
        "categoria": "Moda & Beleza",
        "palavras_secundarias": [
            identidade["rotulo"],
            "visor LCD" if "visor lcd" in _normalizar(nome) else "",
            "sem fio" if "sem fio" in _normalizar(nome) else "",
        ],
        "produto_principal": {
            "nome": nome,
            "link_afiliado": link,
        },
    }
    pauta["palavras_secundarias"] = [
        item for item in pauta["palavras_secundarias"] if item
    ]

    seo = {
        "titulo": titulo,
        "slug": _slug(titulo),
        "meta_description": descricao,
    }

    imagem = {
        "gerada": False,
        "url_publica": "",
        "nome_arquivo": f"{_slug(identidade['rotulo']) or 'produto'}.jpg",
        "alt_text": nome[:125],
        "origem": "sem_imagem_confirmada",
    }

    if (
        produto_principal.get("imagem_verificada")
        and str(produto_principal.get("imagem_produto", "")).startswith("https://")
    ):
        imagem["url_publica"] = produto_principal["imagem_produto"]
        imagem["origem"] = "imagem_real_verificada_do_produto"

    artigo = {
        "titulo": titulo,
        "categoria": "Moda & Beleza",
        "conteudo_html": conteudo_html,
        "links_internos": [],
        "produto_principal": produto_principal,
        "produtos_complementares": [],
        "produtos_afiliados": [produto_principal],
        "modo_fact_safe": True,
    }

    pacote = {
        "pauta": pauta,
        "seo": seo,
        "artigo": artigo,
        "imagem": imagem,
    }

    validacao = validar_pacote_wordpress(pacote)
    if not validacao.get("aprovado"):
        problemas = "; ".join(
            f"{item.get('tipo', 'Risco')}: {item.get('trecho', '')}"
            for item in validacao.get("problemas", [])
        )
        raise RuntimeError(
            "Template fact-safe reprovado pela validação WordPress: "
            + problemas
        )

    pacote["validacao_wordpress"] = validacao
    return pacote
