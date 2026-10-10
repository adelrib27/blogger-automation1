from gerar_artigo import validar_artigo


def montar_artigo(conteudo):
    return {
        "titulo": "Como organizar alimentos na cozinha",
        "palavra_chave": "organizar alimentos",
        "categoria": "Cozinha",
        "conteudo_html": conteudo,
        "fonte": "gemini",
        "produto_principal": "",
    }


def executar_teste(nome, conteudo, deve_passar):
    artigo = montar_artigo(conteudo)
    resultado = validar_artigo(artigo)

    passou = resultado["valido"]

    print("\n" + "=" * 60)
    print(nome)
    print("=" * 60)
    print("Validação:", passou)

    if resultado["erros"]:
        print("Motivos:")
        for erro in resultado["erros"]:
            print("-", erro)

    if passou != deve_passar:
        raise AssertionError(
            f"{nome}: resultado inesperado. "
            f"Esperado={deve_passar}, obtido={passou}"
        )

    print("RESULTADO DO TESTE: OK")


def texto_base(paragrafo_especial):
    introducao = """
<p>Organizar alimentos pode facilitar a rotina da cozinha.
A disposição dos itens pode ser adaptada ao espaço disponível
e aos hábitos de cada casa.</p>
"""

    secao_1 = """
<h2>Planejamento da organização</h2>
<p>Antes de reorganizar o ambiente, observe quais itens são
utilizados com maior frequência. Separar os produtos por tipo
pode tornar a visualização mais simples durante a rotina.</p>
"""

    secao_2 = f"""
<h2>Cuidados durante o armazenamento</h2>
<p>{paragrafo_especial}</p>
"""

    secao_3 = """
<h2>Adaptação à rotina da casa</h2>
<p>A organização pode variar conforme o espaço, os recipientes
disponíveis e as necessidades dos moradores. Quando houver
instruções específicas de conservação, consulte as orientações
do fabricante do produto.</p>
"""

    preenchimento = """
<p>Uma maneira prática de começar é revisar os itens existentes
antes de escolher onde cada grupo ficará. Produtos usados com
frequência podem permanecer em locais de acesso simples, enquanto
itens utilizados ocasionalmente podem ocupar áreas menos
disputadas. Essa distribuição pode ser ajustada sempre que a
rotina mudar.</p>

<p>Também é útil evitar o acúmulo de objetos que já não fazem
sentido para o ambiente. A intenção não é criar uma organização
rígida, mas encontrar uma disposição que seja compreensível para
quem utiliza o espaço diariamente.</p>
"""

    corpo_extra = preenchimento * 7

    return (
        introducao
        + secao_1
        + secao_2
        + secao_3
        + corpo_extra
    )


def main():
    print("=== TESTE ISOLADO DA TRAVA EDITORIAL ===")
    print("Nenhum conteúdo será enviado ao Blogger.")

    seguro = texto_base(
        "Recipientes podem ajudar na organização dos alimentos. "
        "A forma adequada de armazenamento depende do alimento, "
        "das condições do ambiente e das orientações aplicáveis."
    )

    prazo_sensivel = texto_base(
        "Depois de preparado, o alimento pode ficar na geladeira "
        "por até 4 dias e no congelador por até 3 meses."
    )

    alegacao_saude = texto_base(
        "Esse método elimina bactérias e garante que os alimentos "
        "fiquem totalmente seguros para consumo."
    )

    executar_teste(
        "TESTE 1 — CONTEÚDO SEGURO",
        seguro,
        True,
    )

    executar_teste(
        "TESTE 2 — PRAZO NUMÉRICO SENSÍVEL",
        prazo_sensivel,
        False,
    )

    executar_teste(
        "TESTE 3 — ALEGAÇÃO DE SAÚDE/SEGURANÇA",
        alegacao_saude,
        False,
    )

    print("\n" + "=" * 60)
    print("TODOS OS TESTES DA TRAVA EDITORIAL PASSARAM")
    print("=" * 60)


if __name__ == "__main__":
    main()
