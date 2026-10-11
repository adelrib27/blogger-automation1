import html, io, json, os, re, sys, unicodedata
from difflib import SequenceMatcher
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

import requests
import cloudinary
import cloudinary.uploader
from PIL import Image

BASE_DIR = Path(__file__).resolve().parent.parent
CATALOGO_PATH = BASE_DIR / "data" / "produtos.json"
SAIDA_PATH = BASE_DIR / "data" / "produtos_enriquecidos_laboratorio.json"
RELATORIO_PATH = BASE_DIR / "data" / "relatorio_enriquecimento_laboratorio.json"

TIMEOUT = 25
LIMIAR_APROVACAO = 0.58
MAX_IMAGEM_BYTES = 15 * 1024 * 1024
PASTA_CLOUDINARY = "blogger-automation/laboratorio-produtos"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
}

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
    if not a or not b:
        return 0.0
    seq = SequenceMatcher(None, a, b).ratio()
    ta, tb = tokens(a), tokens(b)
    cobertura = len(ta & tb) / max(1, len(ta))
    return round(0.35 * seq + 0.65 * cobertura, 4)

def extrair_product_id(url):
    for padrao in (
        r"/pdp/[^/?#]*-(\d{10,})",
        r"/product/[^/?#]*-(\d{10,})",
        r"/(\d{10,})(?:[/?#]|$)",
    ):
        m = re.search(padrao, url or "")
        if m:
            return m.group(1)
    return ""

def extrair_og_info(url):
    try:
        valores = parse_qs(urlparse(url).query).get("og_info", [])
    except Exception:
        return {}
    for valor in valores:
        for candidato in (valor, unquote(valor)):
            try:
                dado = json.loads(candidato)
                if isinstance(dado, dict):
                    return dado
            except Exception:
                pass
    return {}

def meta(texto, propriedade):
    padroes = (
        rf'<meta[^>]+property=["\']{re.escape(propriedade)}["\'][^>]+content=["\']([^"\']+)["\']',
        rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']{re.escape(propriedade)}["\']',
    )
    for padrao in padroes:
        m = re.search(padrao, texto or "", re.I)
        if m:
            return html.unescape(m.group(1)).strip()
    return ""

def descobrir_dados(link):
    sessao = requests.Session()
    sessao.headers.update(HEADERS)
    resposta = sessao.get(link, allow_redirects=True, timeout=TIMEOUT)
    resposta.raise_for_status()
    urls = [r.url for r in resposta.history] + [resposta.url]

    info = {}
    for url in reversed(urls):
        info = extrair_og_info(url)
        if info:
            break

    titulo = str(info.get("title") or info.get("og_title") or "").strip() if info else ""
    imagem = str(info.get("image") or info.get("image_url") or info.get("og_image") or "").strip() if info else ""

    if not titulo:
        titulo = meta(resposta.text, "og:title")
    if not imagem:
        imagem = meta(resposta.text, "og:image")

    pid = ""
    for url in reversed(urls):
        pid = extrair_product_id(url)
        if pid:
            break

    return {
        "url_final": resposta.url,
        "product_id": pid,
        "titulo": titulo,
        "imagem_origem": imagem if imagem.startswith(("https://", "http://")) else "",
    }

def baixar_e_validar_imagem(url):
    resposta = requests.get(url, headers=HEADERS, timeout=TIMEOUT, stream=True)
    resposta.raise_for_status()

    tipo = (resposta.headers.get("Content-Type") or "").lower()
    if tipo and not tipo.startswith("image/"):
        raise ValueError(f"Content-Type inesperado: {tipo}")

    conteudo = bytearray()
    for bloco in resposta.iter_content(64 * 1024):
        if bloco:
            conteudo.extend(bloco)
            if len(conteudo) > MAX_IMAGEM_BYTES:
                raise ValueError("Imagem excede limite de 15 MB.")

    if not conteudo:
        raise ValueError("Imagem vazia.")

    img = Image.open(io.BytesIO(conteudo))
    img.verify()

    img = Image.open(io.BytesIO(conteudo))
    largura, altura = img.size
    formato = img.format or "desconhecido"

    if largura < 200 or altura < 200:
        raise ValueError(f"Imagem pequena demais: {largura}x{altura}")

    return bytes(conteudo), largura, altura, formato

def configurar_cloudinary():
    if not os.environ.get("CLOUDINARY_URL"):
        raise RuntimeError("Secret CLOUDINARY_URL não encontrado.")
    cloudinary.config(secure=True)

def enviar_cloudinary(conteudo, product_id):
    public_id = f"{PASTA_CLOUDINARY}/{product_id}"
    resultado = cloudinary.uploader.upload(
        io.BytesIO(conteudo),
        public_id=public_id,
        overwrite=True,
        resource_type="image",
        unique_filename=False,
        use_filename=False,
        invalidate=False,
    )
    url = resultado.get("secure_url") or ""
    if not url:
        raise RuntimeError("Cloudinary não retornou secure_url.")
    return url, resultado.get("public_id", public_id)

def main():
    print("=" * 68)
    print("LABORATÓRIO — ENRIQUECIMENTO + CLOUDINARY")
    print("Não altera produtos.json. Não chama Blogger. Não publica.")
    print("=" * 68)

    configurar_cloudinary()

    if not CATALOGO_PATH.exists():
        raise FileNotFoundError(f"Catálogo não encontrado: {CATALOGO_PATH}")

    produtos = json.loads(CATALOGO_PATH.read_text(encoding="utf-8"))
    saida = []
    relatorio = []
    cache_por_product_id = {}

    for indice, produto in enumerate(produtos, 1):
        novo = dict(produto)
        registro = {
            "nome": produto.get("nome", ""),
            "status": "IGNORADO",
            "product_id": "",
            "score": 0.0,
            "imagem_cloudinary": "",
            "erro": "",
        }

        if not produto.get("ativo", True):
            saida.append(novo)
            relatorio.append(registro)
            continue

        nome = str(produto.get("nome", "")).strip()
        link = str(produto.get("link_afiliado", "")).strip()

        print(f"\n[{indice}/{len(produtos)}] {nome}")

        try:
            dados = descobrir_dados(link)
            score = pontuar(nome, dados["titulo"])
            registro["product_id"] = dados["product_id"]
            registro["score"] = score

            print(" Product ID:", dados["product_id"] or "não encontrado")
            print(" Título:", dados["titulo"] or "não encontrado")
            print(" Correspondência:", f"{score:.0%}")

            if not dados["product_id"]:
                raise ValueError("Product ID não encontrado.")
            if not dados["titulo"]:
                raise ValueError("Título do anúncio não encontrado.")
            if not dados["imagem_origem"]:
                raise ValueError("Imagem real não encontrada.")
            if score < LIMIAR_APROVACAO:
                raise ValueError(f"Correspondência insuficiente: {score:.0%}")

            pid = dados["product_id"]

            # Se outro link do catálogo aponta para o mesmo produto,
            # reutiliza a imagem já enviada e evita upload duplicado.
            if pid in cache_por_product_id:
                cached = cache_por_product_id[pid]
                imagem_cloudinary = cached["imagem_cloudinary"]
                public_id = cached["cloudinary_public_id"]
                largura = cached["largura"]
                altura = cached["altura"]
                formato = cached["formato"]
                duplicado = True
                print(" Duplicado detectado: reutilizando imagem já enviada.")
            else:
                conteudo, largura, altura, formato = baixar_e_validar_imagem(dados["imagem_origem"])
                imagem_cloudinary, public_id = enviar_cloudinary(conteudo, pid)
                duplicado = False
                cache_por_product_id[pid] = {
                    "imagem_cloudinary": imagem_cloudinary,
                    "cloudinary_public_id": public_id,
                    "largura": largura,
                    "altura": altura,
                    "formato": formato,
                }

            novo.update({
                "tiktok_product_id": pid,
                "titulo_tiktok": dados["titulo"],
                "imagem_produto": imagem_cloudinary,
                "imagem_verificada": True,
                "correspondencia_imagem": score,
            })

            registro.update({
                "status": "APROVADO",
                "imagem_cloudinary": imagem_cloudinary,
                "cloudinary_public_id": public_id,
                "largura": largura,
                "altura": altura,
                "formato": formato,
                "duplicado_product_id": duplicado,
            })

            print(f" Imagem validada: {largura}x{altura} {formato}")
            print(" Cloudinary: OK")
            print(" RESULTADO: APROVADO")

        except Exception as erro:
            novo["imagem_verificada"] = False
            registro["status"] = "REJEITADO"
            registro["erro"] = f"{type(erro).__name__}: {erro}"
            print(" RESULTADO: REJEITADO")
            print(" Motivo:", registro["erro"])

        saida.append(novo)
        relatorio.append(registro)

    SAIDA_PATH.parent.mkdir(parents=True, exist_ok=True)
    SAIDA_PATH.write_text(
        json.dumps(saida, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    aprovados = sum(r["status"] == "APROVADO" for r in relatorio)
    rejeitados = sum(r["status"] == "REJEITADO" for r in relatorio)
    duplicados = sum(bool(r.get("duplicado_product_id")) for r in relatorio)

    resumo = {
        "modo": "laboratorio",
        "catalogo_original_alterado": False,
        "blogger_chamado": False,
        "total": len(produtos),
        "aprovados": aprovados,
        "rejeitados": rejeitados,
        "duplicados_reutilizados": duplicados,
        "taxa_aprovacao": round(aprovados / max(1, len(produtos)), 4),
        "resultados": relatorio,
    }
    RELATORIO_PATH.write_text(
        json.dumps(resumo, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("\n" + "=" * 68)
    print("RESUMO")
    print("=" * 68)
    print("Total:", len(produtos))
    print("Aprovados:", aprovados)
    print("Rejeitados:", rejeitados)
    print("Duplicados reutilizados:", duplicados)
    print("Taxa:", f'{resumo["taxa_aprovacao"]:.1%}')
    print("Catálogo enriquecido (cópia):", SAIDA_PATH)
    print("Relatório:", RELATORIO_PATH)
    print("CONFIRMAÇÃO: produtos.json permaneceu intocado; Blogger não foi chamado.")

if __name__ == "__main__":
    main()
