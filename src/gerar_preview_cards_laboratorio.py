import html
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CATALOGO = BASE_DIR / "data" / "produtos_enriquecidos_laboratorio.json"
SAIDA = BASE_DIR / "data" / "preview_cards_produtos.html"

def esc(v):
    return html.escape(str(v or ""), quote=True)

def card(p):
    nome = esc(p.get("nome"))
    link = esc(p.get("link_afiliado"))
    imagem = esc(p.get("imagem_produto"))
    foto = ""
    if p.get("imagem_verificada") and imagem:
        foto = '<div class="foto-wrap"><img src="' + imagem + '" alt="' + nome + '" loading="lazy"></div>'
    return (
        '<article class="card">'
        '<div class="selo">🛒 PRODUTO RELACIONADO AO TEMA</div>' + foto +
        '<h2>' + nome + '</h2>'
        '<p class="contexto">Uma opção relacionada ao conteúdo que você acabou de ler. Veja os detalhes do produto diretamente no anúncio.</p>'
        '<p><a class="cta" href="' + link + '" target="_blank" rel="nofollow sponsored noopener">👉 VER PRODUTO E CONFERIR A OFERTA</a></p>'
        '<p class="aviso">Preço, disponibilidade, características e condições podem variar conforme o modelo e o anúncio do vendedor. Confira os detalhes na página do produto antes da compra.</p>'
        '<p class="aviso"><strong>Transparência:</strong> este é um link de afiliado. Se você comprar por meio dele, podemos receber uma comissão, sem custo adicional para você.</p>'
        '</article>'
    )

def main():
    produtos = json.loads(CATALOGO.read_text(encoding="utf-8"))
    ativos = [p for p in produtos if isinstance(p, dict) and p.get("ativo", True)]
    cards = "\n".join(card(p) for p in ativos)
    css = '''
*{box-sizing:border-box}body{margin:0;background:#f1f5f9;color:#111827;font-family:Arial,Helvetica,sans-serif}
.topo,.grade{max-width:900px;margin:auto}.topo{padding:32px 18px 10px}.topo h1{font-size:28px;margin:0 0 8px}.topo p{color:#475569;line-height:1.6}
.grade{padding:18px;display:grid;gap:28px}.card{padding:22px;border:1px solid #e5e7eb;border-radius:14px;background:#f8fafc;text-align:center;box-shadow:0 4px 14px rgba(0,0,0,.08)}
.selo{margin:0 0 16px;font-size:14px;font-weight:700;letter-spacing:.4px}.foto-wrap{width:100%;max-width:300px;height:300px;margin:0 auto 18px;padding:10px;display:flex;align-items:center;justify-content:center;background:#fff;border:1px solid #e5e7eb;border-radius:12px;overflow:hidden}
.foto-wrap img{display:block;width:100%;height:100%;object-fit:contain}h2{margin:0 0 12px;font-size:21px;line-height:1.35}.contexto{margin:0 0 18px;line-height:1.6}
.cta{display:inline-block;padding:14px 22px;background:#16A34A;color:#fff!important;text-decoration:none;font-weight:700;border-radius:10px;font-size:16px;line-height:1.3}.aviso{color:#64748b;font-size:12px;line-height:1.55}
@media(max-width:600px){.grade{padding:14px}.card{padding:18px 14px}.foto-wrap{max-width:260px;height:260px}.cta{display:block;width:100%;padding:14px 12px}}
'''
    pagina = '<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Preview cards</title><style>' + css + '</style></head><body>'
    pagina += '<header class="topo"><h1>Laboratório visual — cards com imagem real</h1><p>' + str(len(ativos)) + ' produtos ativos. Prévia apenas: não publica no Blogger.</p></header><main class="grade">' + cards + '</main></body></html>'
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    SAIDA.write_text(pagina, encoding="utf-8")
    print("Preview criado:", SAIDA)
    print("Cards gerados:", len(ativos))
    print("Nenhuma publicação foi realizada.")

if __name__ == "__main__":
    main()
