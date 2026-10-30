from __future__ import annotations

import html

import automation_rich as impl


_original_rich_product_html = impl.rich_product_html


def rich_product_html(product, copy, image_info, label):
    rendered = _original_rich_product_html(product, copy, image_info, label)
    link = html.escape(str(product.get("offerLink") or "").strip(), quote=True)
    if not link:
        return rendered

    summary_marker = (
        '\n\n  <div style="margin:26px 0;padding:18px 20px;border-radius:14px;'
        'background:#F2FBF7;border:1px solid #d7f0e5;">'
    )
    cta = (
        '\n\n  <div class="conecta-achados-cta-inicial" '
        'style="margin:26px 0 30px;text-align:center;">\n'
        f'    <a href="{link}" target="_blank" rel="nofollow sponsored" '
        'style="display:inline-block;padding:16px 30px;background:#0F8A5F;'
        'color:#ffffff;text-decoration:none;font-weight:700;border-radius:12px;'
        'font-size:17px;box-shadow:0 8px 18px rgba(15,138,95,.16);">'
        'Ver produto na Shopee →</a>\n'
        '  </div>'
    )

    if summary_marker not in rendered:
        raise RuntimeError(
            "Não foi possível posicionar o CTA inicial após o segundo parágrafo."
        )

    return rendered.replace(summary_marker, cta + summary_marker, 1)


impl.rich_product_html = rich_product_html


if __name__ == "__main__":
    impl.main()
