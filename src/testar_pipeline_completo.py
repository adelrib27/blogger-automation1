import main


def executar_teste():
    print()
    print("==========================================")
    print("TESTE — PIPELINE REAL COMPLETO")
    print("MODO DE SEGURANÇA: SOMENTE RASCUNHO")
    print("==========================================")
    print()

    carregar_config_original = main.carregar_config

    def carregar_config_segura():
        config = carregar_config_original()

        # Cria cópias para não alterar o objeto/configuração original.
        config = dict(config)
        config["criar_rascunho_blogger"] = True
        config["publicacao_automatica"] = False

        return config

    # Durante SOMENTE este processo de teste,
    # main.executar() receberá a configuração segura.
    main.carregar_config = carregar_config_segura

    print("TRAVA DE SEGURANÇA APLICADA:")
    print("criar_rascunho_blogger = True")
    print("publicacao_automatica = False")
    print()
    print("Iniciando pipeline real...")
    print()

    pacote = main.executar()

    if not pacote:
        raise RuntimeError(
            "O pipeline terminou sem retornar um pacote."
        )

    blogger = pacote.get("blogger")

    if not blogger:
        raise RuntimeError(
            "O pipeline terminou sem criar o rascunho "
            "no Blogger."
        )

    status = str(
        blogger.get("status", "")
    ).upper()

    if status != "DRAFT":
        raise RuntimeError(
            "TRAVA DE SEGURANÇA: o Blogger não retornou "
            f"status DRAFT. Status recebido: {status}"
        )

    artigo = pacote.get("artigo", {})
    imagem = pacote.get("imagem", {})
    pauta = pacote.get("pauta", {})
    seo = pacote.get("seo", {})

    produto_principal = artigo.get(
        "produto_principal"
    )

    complementares = artigo.get(
        "produtos_complementares",
        [],
    )

    links_internos = artigo.get(
        "links_internos",
        [],
    )

    conteudo_html = artigo.get(
        "conteudo_html",
        "",
    )

    if not produto_principal:
        raise RuntimeError(
            "Produto principal não encontrado "
            "no pacote final."
        )

    if not produto_principal.get("link_afiliado"):
        raise RuntimeError(
            "Produto principal sem link afiliado."
        )

    if (
        produto_principal["link_afiliado"]
        not in conteudo_html
    ):
        raise RuntimeError(
            "O link afiliado principal não está "
            "presente no HTML final."
        )

    if not imagem.get("gerada"):
        raise RuntimeError(
            "A imagem destacada não foi gerada."
        )

    if not imagem.get("url_publica"):
        raise RuntimeError(
            "A imagem não possui URL pública."
        )

    if imagem["url_publica"] not in conteudo_html:
        raise RuntimeError(
            "A imagem destacada não está presente "
            "no HTML final."
        )

    print()
    print("==========================================")
    print("PIPELINE COMPLETO: OK")
    print("BLOGGER: RASCUNHO")
    print("PUBLICAÇÃO AUTOMÁTICA: BLOQUEADA")
    print("==========================================")
    print()

    print("Título:", seo.get("titulo"))
    print(
        "Palavra-chave:",
        pauta.get("palavra_chave"),
    )
    print(
        "Categoria:",
        pauta.get("categoria"),
    )

    print()
    print(
        "Produto principal:",
        produto_principal.get("nome"),
    )
    print(
        "Link afiliado:",
        produto_principal.get("link_afiliado"),
    )

    print()
    print(
        "Produtos complementares:",
        len(complementares),
    )

    for produto in complementares:
        print(
            "-",
            produto.get("nome"),
        )

    print()
    print(
        "Links internos:",
        len(links_internos),
    )

    for link in links_internos:
        print(
            "-",
            link.get("titulo", ""),
        )

    print()
    print(
        "Imagem:",
        imagem.get("url_publica"),
    )

    print()
    print(
        "Post ID:",
        blogger.get("id"),
    )
    print(
        "Status:",
        blogger.get("status"),
    )

    print()
    print(
        "TESTE FINALIZADO COM SEGURANÇA."
    )
    print(
        "Abra o rascunho no Blogger para "
        "a conferência visual final."
    )


if __name__ == "__main__":
    executar_teste()
