import html, json, re, sys, unicodedata
from difflib import SequenceMatcher
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse
import requests

BASE_DIR = Path(__file__).resolve().parent.parent
CATALOGO_PATH = BASE_DIR / "data" / "produtos.json"
RELATORIO_PATH = BASE_DIR / "data" / "laboratorio_imagens_produtos.json"
TIMEOUT = 20
LIMIAR_APROVACAO = 0.58
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36", "Accept-Language": "pt-BR,pt;q=0.9"}

def normalizar(texto):
    texto = html.unescape(str(texto or "")).lower()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = re.sub(r"[^a-z0-9]+", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()

def tokens(texto):
    ignorar = {"de","da","do","das","dos","com","para","e","em","um","uma","o","a","as","os","por"}
    return {t for t in normalizar(texto).split() if len(t) >= 3 and t not in ignorar}

def pontuar(nome, titulo):
    a, b = normalizar(nome), normalizar(titulo)
    if not a or not b: return 0.0
    seq = SequenceMatcher(None, a, b).ratio()
    ta, tb = tokens(a), tokens(b)
    cobertura = len(ta & tb) / max(1, len(ta))
    return round(0.35 * seq + 0.65 * cobertura, 4)

def product_id(url):
    for p in (r"/pdp/[^/?#]*-(\d{10,})", r"/product/[^/?#]*-(\d{10,})", r"/(\d{10,})(?:[/?#]|$)"):
        m = re.search(p, url or "")
        if m: return m.group(1)
    return ""

def og_info(url):
    try: valores = parse_qs(urlparse(url).query).get("og_info", [])
    except Exception: return {}
    for valor in valores:
        for candidato in (valor, unquote(valor)):
            try:
                dado = json.loads(candidato)
                if isinstance(dado, dict): return dado
            except Exception: pass
    return {}

def meta(texto, prop):
    for p in (
        rf'<meta[^>]+property=["\']{re.escape(prop)}["\'][^>]+content=["\']([^"\']+)["\']',
        rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']{re.escape(prop)}["\']',
    ):
        m = re.search(p, texto or "", re.I)
        if m: return html.unescape(m.group(1)).strip()
    return ""

def analisar(p):
    nome, link = str(p.get("nome","")).strip(), str(p.get("link_afiliado","")).strip()
    r = {"nome_catalogo":nome,"link_afiliado":link,"url_final":"","product_id":"","titulo_tiktok":"","imagem_real":"","pontuacao_correspondencia":0.0,"aprovado":False,"origem_imagem":"","erro":""}
    try:
        s = requests.Session(); s.headers.update(HEADERS)
        resp = s.get(link, allow_redirects=True, timeout=TIMEOUT)
        r["url_final"] = resp.url
        urls = [x.url for x in resp.history] + [resp.url]
        info = {}
        for u in reversed(urls):
            info = og_info(u)
            if info: break
        titulo = str(info.get("title") or info.get("og_title") or "").strip() if info else ""
        imagem = str(info.get("image") or info.get("image_url") or info.get("og_image") or "").strip() if info else ""
        if imagem.startswith(("http://","https://")): r["origem_imagem"] = "og_info"
        if not titulo: titulo = meta(resp.text, "og:title")
        if not imagem:
            imagem = meta(resp.text, "og:image")
            if imagem: r["origem_imagem"] = "og:image"
        r["titulo_tiktok"] = titulo
        r["imagem_real"] = imagem if imagem.startswith(("http://","https://")) else ""
        for u in reversed(urls):
            pid = product_id(u)
            if pid: r["product_id"] = pid; break
        r["pontuacao_correspondencia"] = pontuar(nome, titulo)
        r["aprovado"] = bool(r["imagem_real"] and titulo and r["pontuacao_correspondencia"] >= LIMIAR_APROVACAO)
        if not r["aprovado"]:
            motivos=[]
            if not titulo: motivos.append("título não encontrado")
            if not r["imagem_real"]: motivos.append("imagem não encontrada")
            if titulo and r["pontuacao_correspondencia"] < LIMIAR_APROVACAO: motivos.append("correspondência insuficiente")
            r["erro"]="; ".join(motivos)
    except Exception as e:
        r["erro"] = f"{type(e).__name__}: {e}"
    return r

def main():
    produtos = json.loads(CATALOGO_PATH.read_text(encoding="utf-8"))
    ativos = [p for p in produtos if isinstance(p,dict) and p.get("ativo",True)]
    print("=== LABORATÓRIO — IMAGENS REAIS TIKTOK SHOP ===")
    print("Somente leitura: não altera catálogo e não publica.\n")
    resultados=[]
    for i,p in enumerate(ativos,1):
        r=analisar(p); resultados.append(r)
        print(f'[{i}/{len(ativos)}] {r["nome_catalogo"]}')
        print(" Product ID:", r["product_id"] or "não encontrado")
        print(" Título:", r["titulo_tiktok"] or "não encontrado")
        print(" Imagem:", "ENCONTRADA" if r["imagem_real"] else "não encontrada")
        print(" Correspondência:", f'{r["pontuacao_correspondencia"]:.0%}')
        print(" RESULTADO:", "APROVADO" if r["aprovado"] else "REJEITADO")
        if r["erro"]: print(" Motivo:", r["erro"])
        print()
    aprov=sum(x["aprovado"] for x in resultados)
    rel={"modo":"laboratorio_somente_leitura","total":len(resultados),"product_ids_encontrados":sum(bool(x["product_id"]) for x in resultados),"imagens_encontradas":sum(bool(x["imagem_real"]) for x in resultados),"aprovados":aprov,"taxa_aprovacao":round(aprov/max(1,len(resultados)),4),"resultados":resultados}
    RELATORIO_PATH.parent.mkdir(parents=True,exist_ok=True)
    RELATORIO_PATH.write_text(json.dumps(rel,ensure_ascii=False,indent=2),encoding="utf-8")
    print("=== RESUMO ===")
    print("Total:",rel["total"]); print("Product IDs:",rel["product_ids_encontrados"]); print("Imagens:",rel["imagens_encontradas"]); print("Aprovados:",aprov); print("Taxa:",f'{rel["taxa_aprovacao"]:.1%}')
    print("Relatório:",RELATORIO_PATH)
    print("Nenhum catálogo foi alterado e nada foi publicado.")

if __name__ == "__main__":
    main()
