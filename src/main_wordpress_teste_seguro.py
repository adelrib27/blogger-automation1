import os
import re
import unicodedata

import gerar_pautas
import validacao_wordpress
import fact_safe_wordpress
import main_wordpress


REGRAS_TESTE_APARELHOS_BELEZA = """

REGRAS REFORÇADAS PARA APARELHOS DE BELEZA — RADAR TECH BR:
- Quando o produto for máquina de cortar cabelo, barbeador, shaver, chapinha,
  prancha ou aparador, escreva estritamente como CHECKLIST/GUIA DE COMPRA.
- Use como fatos do produto somente características literalmente presentes no
  nome fornecido pelo catálogo. Todo o restante deve ser apresentado como algo
  que o leitor precisa CONFERIR no anúncio, na ficha técnica ou no manual.
- Não diga que bateria, motor, lâmina, peso, formato, visor, cabo, acabamento
  ou qualquer recurso oferece mais precisão, conforto, eficiência, segurança,
  durabilidade, facilidade, mobilidade ou melhor resultado sem fonte explícita.
- Não forneça autonomia típica, tempo de carga, vida útil, rotação, potência,
  material de lâmina, nível de ruído, peso, dimensões ou qualquer faixa genérica.
- Não use frases como "alguns modelos", "a maioria dos modelos", "geralmente"
  ou "normalmente" para introduzir especificações que não constam no catálogo.
- Não recomende modelo, lâmina, regulagem ou acessório com base em tipo de
  cabelo, textura do fio, tipo de pele, densidade de barba ou sensibilidade.
- Não ensine limpeza, lubrificação, armazenamento, troca de lâmina ou cuidado de
  bateria. Oriente apenas a seguir as instruções específicas do fabricante.
- Se o nome disser apenas "visor LCD", não presuma o que o visor exibe. Não
  liste bateria, velocidade, temperatura, comprimento, zoom ou qualquer outra
  função possível; diga somente para conferir no anúncio/manual o que ele mostra.
- Para "máquina de cortar cabelo", não amplie o uso para barba, sobrancelhas,
  pelos corporais ou outras áreas se isso não estiver explícito no nome.
- Prefira seções seguras como: "o que o nome do anúncio confirma", "o que
  conferir antes da compra", "perguntas para fazer ao vendedor", "itens da
  ficha técnica que merecem verificação" e "como comparar anúncios sem assumir
  especificações".
"""

REGRAS_TESTE_PAUTA = """

REGRAS REFORÇADAS DE PAUTA PARA APARELHOS DE BELEZA:
- A pauta deve permanecer no uso explicitamente indicado pelo nome do produto.
  Se o produto diz "máquina de cortar cabelo", não crie pauta sobre barba,
  sobrancelha, depilação, pele ou tratamento capilar.
- Não gere pautas centradas em autonomia, bateria, potência, ergonomia, ruído,
  manutenção, durabilidade, tipo de cabelo ou desempenho de lâmina quando o
  catálogo não fornece esses dados.
- Para um produto cujo nome informa "sem fio" e "visor LCD", prefira pauta de
  checklist pré-compra e verificação do anúncio. Não presuma a função do visor.
- O título e a descrição da pauta não devem prometer precisão, conforto,
  praticidade superior, desempenho ou resultado de corte sem base explícita.
"""


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


def _tokens(texto):
    return {token for token in _normalizar(texto).split() if len(token) >= 3}


def instalar_bloqueio_produto_teste():
    filtro = os.getenv("RADARTECH_TEST_PRODUCT_KEYWORD", "").strip()
    if not filtro:
        return None

    carregar_original = gerar_pautas.carregar_produtos
    produtos = carregar_original()
    filtro_norm = _normalizar(filtro)
    tokens_filtro = _tokens(filtro)

    correspondencias = [
        produto
        for produto in produtos
        if filtro_norm in _normalizar(produto.get("nome", ""))
    ]

    if not correspondencias and tokens_filtro:
        candidatos = []
        for produto in produtos:
            nome_tokens = _tokens(produto.get("nome", ""))
            comuns = tokens_filtro.intersection(nome_tokens)
            proporcao = len(comuns) / len(tokens_filtro)
            candidatos.append((proporcao, len(comuns), produto))

        candidatos.sort(key=lambda item: (item[0], item[1]), reverse=True)
        melhor_proporcao, melhor_comuns, melhor_produto = candidatos[0]
        if melhor_comuns >= 1 and melhor_proporcao >= 0.50:
            correspondencias = [melhor_produto]

    if not correspondencias:
        raise RuntimeError(
            "Produto de teste não encontrado para bloqueio estrito: " + filtro
        )

    escolhido = max(
        correspondencias,
        key=lambda produto: len(
            tokens_filtro.intersection(_tokens(produto.get("nome", "")))
        ),
    )
    nome_escolhido = str(escolhido.get("nome", "")).strip()

    def carregar_produtos_bloqueado():
        return [dict(escolhido)]

    def ordenar_produtos_bloqueado(produtos_recebidos):
        permitidos = [
            produto
            for produto in produtos_recebidos
            if str(produto.get("nome", "")).strip() == nome_escolhido
        ]
        if not permitidos:
            raise RuntimeError(
                "Produto bloqueado esgotou as tentativas desta rodada. "
                "O teste foi encerrado sem alternar para outro produto."
            )
        return [dict(permitidos[0])]

    gerar_pautas.carregar_produtos = carregar_produtos_bloqueado
    gerar_pautas.ordenar_produtos_para_tentativa = ordenar_produtos_bloqueado

    print("\nBLOQUEIO ESTRITO DE PRODUTO ATIVO")
    print("Produto permitido neste teste:", nome_escolhido)
    print("Nenhum outro produto poderá ser selecionado nesta execução.")

    return dict(escolhido)


def reforcar_prompts():
    if REGRAS_TESTE_APARELHOS_BELEZA not in validacao_wordpress.REGRAS_EXTRAS_PROMPT:
        validacao_wordpress.REGRAS_EXTRAS_PROMPT += REGRAS_TESTE_APARELHOS_BELEZA

    if REGRAS_TESTE_PAUTA not in validacao_wordpress.REGRAS_EXTRAS_PAUTA:
        validacao_wordpress.REGRAS_EXTRAS_PAUTA += REGRAS_TESTE_PAUTA

    print("Regras reforçadas de Moda & Beleza: ATIVAS")


def instalar_modo_fact_safe(produto):
    if not fact_safe_wordpress.produto_requer_modo_fact_safe(produto):
        return False

    def gerar_pacote_fact_safe():
        print("\n=== MODO FACT-SAFE WORDPRESS ===")
        print("Geração editorial por IA: IGNORADA para este produto.")
        print("Fonte factual permitida: nome do catálogo + página/manual para conferência.")
        pacote = fact_safe_wordpress.criar_pacote_fact_safe(
            produto=produto,
            motor=main_wordpress.motor,
            validar_pacote_wordpress=validacao_wordpress.validar_pacote_wordpress,
        )
        print("Template fact-safe validado pela segunda trava editorial.")
        print("Imagem de capa: imagem real verificada do produto, quando disponível.")
        return pacote

    main_wordpress.gerar_pacote_aprovado_wordpress = gerar_pacote_fact_safe
    print("Modo fact-safe estrutural: ATIVO para este produto.")
    return True


def executar():
    reforcar_prompts()
    produto = instalar_bloqueio_produto_teste()
    if produto:
        instalar_modo_fact_safe(produto)
    main_wordpress.executar()


if __name__ == "__main__":
    executar()
