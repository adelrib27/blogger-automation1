from cta_context import CTA_PRODUCT_TITLE_CLASS, cta_block


def main():
    item = {
        "product": "Caixa Ferramentas Sanfonada 7 Gavetas C/Alça Fixa Marcon",
        "affiliate_link": "https://s.shopee.com.br/exemplo",
        "image_url": "https://cf.shopee.com.br/file/exemplo",
    }
    lead = (
        "Para quem deseja colocar essas orientações em prática, a Caixa Sanfonada de 7 Gavetas da Marcon "
        "é uma opção relacionada disponível para consulta. Confira as especificações do modelo no anúncio "
        "para avaliar se ele atende à sua necessidade; você também pode consultar o modelo na Shopee."
    )
    block = cta_block(item, lead)
    title = item["product"]

    assert block.count(f'class="{CTA_PRODUCT_TITLE_CLASS}"') == 1
    image_pos = block.index("<img ")
    title_pos = block.index(f'class="{CTA_PRODUCT_TITLE_CLASS}"')
    lead_pos = block.index("Para quem")
    assert image_pos < title_pos < lead_pos
    assert f'>{title}</p>' in block
    assert f"<h2>{title}</h2>" not in block and f"<h3>{title}</h3>" not in block

    print("CTA card Radar Tech BR: 4/4 OK — imagem -> título original -> chamada; sem H2/H3 comercial.")


if __name__ == "__main__":
    main()
