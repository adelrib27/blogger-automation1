import base64
import os
import re
import time
import unicodedata
from io import BytesIO
from pathlib import Path

import cloudinary
import cloudinary.uploader
import requests
from PIL import Image


# ============================================================
# CONFIGURAÇÃO
# ============================================================

MODELO_IMAGEM = "@cf/black-forest-labs/flux-2-klein-4b"

PASTA_IMAGENS = Path("data/imagens")

FORMATO_IMAGEM = "16:9"
RESOLUCAO_IMAGEM = "1280x720"
MIME_TYPE = "image/jpeg"

LARGURA_FINAL = 1280
ALTURA_FINAL = 720

TIMEOUT_CLOUDFLARE = 180
TENTATIVAS_CLOUDFLARE = 3


# ============================================================
# FUNÇÕES BÁSICAS
# ============================================================

def limpar_texto(texto):
    if not texto:
        return ""

    return re.sub(
        r"\s+",
        " ",
        str(texto),
    ).strip()


def criar_slug(texto):
    """
    Cria um slug simples e seguro.
    """

    texto = limpar_texto(texto).lower()

    texto = unicodedata.normalize(
        "NFKD",
        texto,
    )

    texto = "".join(
        caractere
        for caractere in texto
        if not unicodedata.combining(
            caractere
        )
    )

    texto = re.sub(
        r"[^a-z0-9\s-]",
        "",
        texto,
    )

    texto = re.sub(
        r"[\s_-]+",
        "-",
        texto,
    )

    return texto.strip("-")


def criar_nome_arquivo(titulo):
    """
    Cria um nome de arquivo amigável para SEO.
    """

    slug = criar_slug(titulo)

    if not slug:
        slug = "imagem-destacada"

    return f"{slug[:80]}.jpg"


def criar_alt_text(
    titulo,
    palavra_chave,
):
    """
    Cria texto alternativo para
    acessibilidade e SEO.
    """

    titulo = limpar_texto(titulo)

    palavra_chave = limpar_texto(
        palavra_chave
    )

    if palavra_chave:
        return (
            f"{titulo} - {palavra_chave}"
        )[:125]

    return titulo[:125]


# ============================================================
# PROMPT DA IMAGEM
# ============================================================

def criar_prompt_imagem(
    titulo,
    palavra_chave,
    categoria="Casa e Decoração",
):
    """
    Cria o prompt editorial para
    a imagem destacada do artigo.
    """

    titulo = limpar_texto(titulo)

    palavra_chave = limpar_texto(
        palavra_chave
    )

    categoria = limpar_texto(categoria)

    prompt = f"""
Fotografia editorial ultra-realista para ser a imagem destacada
de um artigo brasileiro sobre Casa e Decoração.

TÍTULO DO ARTIGO:
{titulo}

ASSUNTO PRINCIPAL:
{palavra_chave}

CATEGORIA:
{categoria}

A fotografia deve representar diretamente o assunto descrito
no título. Não produzir uma decoração genérica que não tenha
relação clara com o tema.

Criar uma cena residencial brasileira moderna, realista,
elegante, acolhedora e perfeitamente possível de existir
em uma casa real.

O elemento relacionado ao assunto principal deve estar
claramente perceptível.

COMPOSIÇÃO:

Criar a cena pensando em um enquadramento horizontal amplo
para capa de artigo de blog.

O assunto principal deve permanecer preferencialmente na
região central da composição.

Preservar espaço visual suficiente nas laterais e evitar
colocar elementos essenciais muito próximos das bordas,
pois a imagem será posteriormente adaptada para 16:9.

ESTILO VISUAL:

- fotografia editorial profissional;
- aparência totalmente fotorrealista;
- ambiente residencial brasileiro;
- decoração contemporânea e acessível;
- materiais e texturas naturais;
- móveis em escala realista;
- arquitetura plausível;
- iluminação natural ou coerente com o ambiente;
- sombras naturais;
- profundidade fotográfica realista;
- composição limpa;
- alto nível de detalhes;
- aparência de fotografia profissional de interiores;
- nenhuma aparência de ilustração ou render artificial.

NÃO INCLUIR:

- pessoas;
- textos;
- títulos;
- letras;
- palavras;
- números;
- logotipos;
- marcas comerciais;
- marcas-d'água;
- preços;
- etiquetas;
- interfaces;
- banners;
- molduras;
- colagens;
- montagens;
- desenhos;
- ilustrações;
- aparência CGI;
- aparência 3D artificial;
- objetos deformados;
- arquitetura impossível.

A imagem deve parecer uma fotografia real produzida
profissionalmente para um blog brasileiro de Casa e Decoração.
"""

    return limpar_texto(prompt)


# ============================================================
# PREPARAÇÃO DOS METADADOS
# ============================================================

def preparar_imagem(
    titulo,
    palavra_chave,
    categoria="Casa e Decoração",
):
    """
    Monta as informações necessárias
    para a imagem destacada.

    Esta função permanece compatível
    com o main.py existente.
    """

    return {
        "nome_arquivo": criar_nome_arquivo(
            titulo
        ),
        "alt_text": criar_alt_text(
            titulo,
            palavra_chave,
        ),
        "prompt": criar_prompt_imagem(
            titulo,
            palavra_chave,
            categoria,
        ),
        "formato": FORMATO_IMAGEM,
        "resolucao": RESOLUCAO_IMAGEM,
        "tipo": "imagem_destacada",
    }


# ============================================================
# TRATAMENTO DE ERROS
# ============================================================

def erro_de_cota(erro):
    """
    Detecta erros relacionados a cota,
    limite ou excesso de requisições.
    """

    texto = str(erro).lower()

    termos = (
        "429",
        "quota",
        "rate limit",
        "rate_limit",
        "too many requests",
        "limit exceeded",
    )

    return any(
        termo in texto
        for termo in termos
    )


def erro_temporario(erro):
    """
    Detecta erros temporários que podem
    justificar nova tentativa.
    """

    texto = str(erro).lower()

    termos = (
        "500",
        "502",
        "503",
        "504",
        "timeout",
        "timed out",
        "temporarily unavailable",
        "internal error",
        "connection error",
        "connection reset",
    )

    return any(
        termo in texto
        for termo in termos
    )


# ============================================================
# CLOUDFLARE WORKERS AI
# ============================================================

def gerar_bytes_cloudflare(
    prompt,
):
    """
    Solicita uma imagem ao Cloudflare
    Workers AI usando FLUX.
    """

    account_id = os.getenv(
        "CLOUDFLARE_ACCOUNT_ID"
    )

    api_token = os.getenv(
        "CLOUDFLARE_API_TOKEN"
    )

    if not account_id:
        raise RuntimeError(
            "CLOUDFLARE_ACCOUNT_ID "
            "não encontrado nos Secrets."
        )

    if not api_token:
        raise RuntimeError(
            "CLOUDFLARE_API_TOKEN "
            "não encontrado nos Secrets."
        )

    url = (
        "https://api.cloudflare.com/client/v4/"
        f"accounts/{account_id}/ai/run/"
        f"{MODELO_IMAGEM}"
    )

    headers = {
        "Authorization": (
            f"Bearer {api_token}"
        ),
    }

    arquivos = {
        "prompt": (
            None,
            prompt,
        ),
    }

    resposta = requests.post(
        url,
        headers=headers,
        files=arquivos,
        timeout=TIMEOUT_CLOUDFLARE,
    )

    print(
        "HTTP Cloudflare:",
        resposta.status_code,
    )

    if resposta.status_code != 200:
        corpo = resposta.text[:2000]

        raise RuntimeError(
            "Cloudflare retornou "
            f"HTTP {resposta.status_code}: "
            f"{corpo}"
        )

    content_type = resposta.headers.get(
        "content-type",
        "",
    ).lower()

    if content_type.startswith(
        "image/"
    ):
        return resposta.content

    if "application/json" in content_type:
        dados = resposta.json()

        if not dados.get(
            "success",
            False,
        ):
            raise RuntimeError(
                "Cloudflare informou falha: "
                f"{dados}"
            )

        resultado = (
            dados.get("result")
            or {}
        )

        imagem_base64 = resultado.get(
            "image"
        )

        if not imagem_base64:
            raise RuntimeError(
                "Cloudflare retornou JSON, "
                "mas result.image não foi "
                "encontrado."
            )

        try:
            return base64.b64decode(
                imagem_base64,
                validate=True,
            )

        except Exception as erro:
            raise RuntimeError(
                "Não foi possível decodificar "
                "a imagem Base64 retornada "
                "pela Cloudflare."
            ) from erro

    raise RuntimeError(
        "Formato inesperado retornado "
        "pela Cloudflare: "
        f"{content_type}"
    )


# ============================================================
# CONVERSÃO PARA 16:9
# ============================================================

def salvar_imagem_16_9(
    bytes_imagem,
    caminho,
):
    """
    Centraliza o corte da imagem e cria
    um JPEG final 1280x720.
    """

    with Image.open(
        BytesIO(bytes_imagem)
    ) as imagem:

        imagem = imagem.convert("RGB")

        largura_original = imagem.width
        altura_original = imagem.height

        print(
            "Dimensões recebidas:",
            f"{largura_original}x"
            f"{altura_original}",
        )

        proporcao_atual = (
            largura_original
            / altura_original
        )

        proporcao_desejada = (
            LARGURA_FINAL
            / ALTURA_FINAL
        )

        if (
            proporcao_atual
            > proporcao_desejada
        ):
            nova_largura = int(
                altura_original
                * proporcao_desejada
            )

            esquerda = (
                largura_original
                - nova_largura
            ) // 2

            caixa = (
                esquerda,
                0,
                esquerda + nova_largura,
                altura_original,
            )

        else:
            nova_altura = int(
                largura_original
                / proporcao_desejada
            )

            topo = (
                altura_original
                - nova_altura
            ) // 2

            caixa = (
                0,
                topo,
                largura_original,
                topo + nova_altura,
            )

        imagem = imagem.crop(
            caixa
        )

        imagem = imagem.resize(
            (
                LARGURA_FINAL,
                ALTURA_FINAL,
            ),
            Image.Resampling.LANCZOS,
        )

        imagem.save(
            caminho,
            format="JPEG",
            quality=92,
            optimize=True,
        )

    if not caminho.exists():
        raise RuntimeError(
            "A imagem final não foi criada."
        )

    tamanho = caminho.stat().st_size

    if tamanho < 1000:
        raise RuntimeError(
            "A imagem final parece "
            f"inválida: {tamanho} bytes."
        )

    print(
        "Conversão 16:9 concluída:",
        f"{LARGURA_FINAL}x"
        f"{ALTURA_FINAL}",
    )

    return tamanho


# ============================================================
# CLOUDINARY
# ============================================================

def enviar_para_cloudinary(
    caminho,
    nome_arquivo,
):
    """
    Envia a imagem final ao Cloudinary
    e devolve a URL HTTPS pública.
    """

    cloudinary_url = os.getenv(
        "CLOUDINARY_URL"
    )

    if not cloudinary_url:
        raise RuntimeError(
            "CLOUDINARY_URL não encontrado "
            "nos Secrets."
        )

    cloudinary.config(
        secure=True
    )

    nome_sem_extensao = Path(
        nome_arquivo
    ).stem

    public_id = (
        "blogger-automation/"
        f"{nome_sem_extensao}"
    )

    resultado = (
        cloudinary.uploader.upload(
            str(caminho),
            public_id=public_id,
            overwrite=True,
            resource_type="image",
        )
    )

    url_publica = resultado.get(
        "secure_url"
    )

    if not url_publica:
        raise RuntimeError(
            "Cloudinary não retornou "
            "secure_url."
        )

    return url_publica


# ============================================================
# GERAÇÃO DA IMAGEM DESTACADA
# ============================================================

def gerar_imagem_destacada(
    titulo,
    palavra_chave,
    categoria="Casa e Decoração",
    pasta_saida=None,
):
    """
    Fluxo completo:

    Cloudflare FLUX
    -> conversão 16:9
    -> arquivo JPEG 1280x720
    -> Cloudinary
    -> URL pública

    Se ocorrer uma falha, devolve resultado
    seguro em vez de derrubar a automação.
    """

    dados = preparar_imagem(
        titulo=titulo,
        palavra_chave=palavra_chave,
        categoria=categoria,
    )

    if pasta_saida is None:
        pasta_saida = PASTA_IMAGENS
    else:
        pasta_saida = Path(
            pasta_saida
        )

    pasta_saida.mkdir(
        parents=True,
        exist_ok=True,
    )

    caminho = (
        pasta_saida
        / dados["nome_arquivo"]
    )

    ultimo_erro = None

    print()
    print(
        "=== GERAÇÃO DE IMAGEM DESTACADA ==="
    )

    print(
        "Modelo:",
        MODELO_IMAGEM,
    )

    print(
        "Arquivo:",
        dados["nome_arquivo"],
    )

    print(
        "Formato final:",
        FORMATO_IMAGEM,
    )

    print(
        "Dimensões finais:",
        RESOLUCAO_IMAGEM,
    )

    print()

    for tentativa in range(
        1,
        TENTATIVAS_CLOUDFLARE + 1,
    ):

        try:
            print(
                "Tentativa Cloudflare:",
                f"{tentativa}/"
                f"{TENTATIVAS_CLOUDFLARE}",
            )

            bytes_imagem = (
                gerar_bytes_cloudflare(
                    dados["prompt"]
                )
            )

            tamanho = salvar_imagem_16_9(
                bytes_imagem=bytes_imagem,
                caminho=caminho,
            )

            print(
                "Imagem local criada:",
                caminho,
            )

            print(
                "Tamanho:",
                f"{tamanho} bytes",
            )

            print()
            print(
                "Enviando imagem "
                "ao Cloudinary..."
            )

            url_publica = (
                enviar_para_cloudinary(
                    caminho=caminho,
                    nome_arquivo=(
                        dados[
                            "nome_arquivo"
                        ]
                    ),
                )
            )

            print(
                "Upload Cloudinary: OK"
            )

            print(
                "URL pública:",
                url_publica,
            )

            print()
            print(
                "Imagem destacada "
                "gerada com sucesso."
            )

            return {
                **dados,
                "gerada": True,
                "modelo": MODELO_IMAGEM,
                "resolucao": (
                    RESOLUCAO_IMAGEM
                ),
                "caminho": str(
                    caminho
                ),
                "tamanho_bytes": tamanho,
                "url_publica": url_publica,
                "erro": None,
            }

        except Exception as erro:
            ultimo_erro = erro

            print()
            print(
                "Falha na geração "
                f"(tentativa {tentativa}/"
                f"{TENTATIVAS_CLOUDFLARE}):"
            )

            print(
                str(erro)
            )

            if erro_de_cota(erro):
                print(
                    "Cota ou limite detectado."
                )

                break

            if (
                erro_temporario(erro)
                and tentativa
                < TENTATIVAS_CLOUDFLARE
            ):
                espera = (
                    5
                    if tentativa == 1
                    else 15
                )

                print(
                    "Erro temporário."
                )

                print(
                    "Nova tentativa em "
                    f"{espera} segundos..."
                )

                time.sleep(
                    espera
                )

                continue

            break

    print()
    print(
        "Não foi possível gerar "
        "a imagem destacada."
    )

    print(
        "A automação poderá continuar "
        "sem imagem."
    )

    return {
        **dados,
        "gerada": False,
        "modelo": MODELO_IMAGEM,
        "caminho": None,
        "tamanho_bytes": 0,
        "url_publica": None,
        "erro": (
            str(ultimo_erro)
            if ultimo_erro
            else "Erro desconhecido."
        ),
    }


# ============================================================
# TESTE ISOLADO
# ============================================================

if __name__ == "__main__":

    print()
    print(
        "TESTE ISOLADO — GERAR_IMAGEM.PY"
    )

    print(
        "Nenhum conteúdo será "
        "enviado ao Blogger."
    )

    resultado = gerar_imagem_destacada(
        titulo=(
            "Iluminação para sala de estar "
            "aconchegante usando luz indireta"
        ),
        palavra_chave=(
            "iluminação para sala"
        ),
        categoria="Iluminação",
    )

    print()
    print(
        "=== RESULTADO DO TESTE ==="
    )

    print(
        "Gerada:",
        resultado["gerada"],
    )

    print(
        "Arquivo:",
        resultado["nome_arquivo"],
    )

    print(
        "ALT:",
        resultado["alt_text"],
    )

    print(
        "Modelo:",
        resultado["modelo"],
    )

    print(
        "Resolução:",
        resultado["resolucao"],
    )

    print(
        "Caminho:",
        resultado["caminho"],
    )

    print(
        "URL pública:",
        resultado["url_publica"],
    )

    if resultado["erro"]:
        print(
            "Erro:",
            resultado["erro"],
        )

    print()
    print(
        "Nenhum conteúdo foi "
        "enviado ao Blogger."
    )
