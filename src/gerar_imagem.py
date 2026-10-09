import base64
import os
import re
import time
import unicodedata
from pathlib import Path

from google import genai
from google.genai import types


# ============================================================
# CONFIGURAÇÃO
# ============================================================

MODELOS_IMAGEM = [
    "gemini-3.1-flash-image",
]

PASTA_IMAGENS = Path("data/imagens")

FORMATO_IMAGEM = "16:9"
RESOLUCAO_IMAGEM = "2K"
MIME_TYPE = "image/jpeg"


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


def criar_nome_arquivo(titulo):
    """
    Cria um nome de arquivo amigável para SEO.

    Exemplo:
    Como Organizar a Cozinha
    ->
    como-organizar-a-cozinha.jpg
    """

    titulo = limpar_texto(titulo).lower()

    titulo = unicodedata.normalize(
        "NFKD",
        titulo,
    )

    titulo = "".join(
        caractere
        for caractere in titulo
        if not unicodedata.combining(
            caractere
        )
    )

    titulo = re.sub(
        r"[^a-z0-9\s-]",
        "",
        titulo,
    )

    titulo = re.sub(
        r"[\s_-]+",
        "-",
        titulo,
    )

    titulo = titulo.strip("-")

    if not titulo:
        titulo = "imagem-destacada"

    return f"{titulo[:80]}.jpg"


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
    Cria um prompt editorial específico
    para a imagem destacada do artigo.
    """

    titulo = limpar_texto(titulo)
    palavra_chave = limpar_texto(
        palavra_chave
    )
    categoria = limpar_texto(categoria)

    prompt = f"""
Crie uma fotografia editorial fotorrealista
para ser a imagem destacada de um artigo
brasileiro sobre Casa e Decoração.

TÍTULO DO ARTIGO:
{titulo}

ASSUNTO PRINCIPAL:
{palavra_chave}

CATEGORIA:
{categoria}

A fotografia deve representar diretamente
o assunto descrito no título, e não apenas
mostrar uma decoração genérica.

Crie uma cena residencial brasileira moderna,
realista, elegante, acolhedora e possível de
existir em uma casa real.

O elemento relacionado ao assunto principal
deve ser claramente perceptível na imagem.

A composição deve ajudar o leitor a entender
visualmente o tema do artigo antes mesmo
de ler o texto.

ESTILO VISUAL:

- fotografia editorial profissional;
- aparência totalmente fotorrealista;
- ambiente residencial brasileiro;
- decoração bonita, contemporânea e acessível;
- materiais e texturas naturais;
- móveis em escala e proporções realistas;
- arquitetura plausível;
- iluminação coerente com o tema;
- profundidade fotográfica natural;
- composição limpa e elegante;
- aparência de fotografia de revista de
  decoração;
- detalhes realistas;
- alta qualidade visual.

COMPOSIÇÃO:

- enquadramento horizontal;
- formato adequado para capa de artigo;
- assunto principal claramente visível;
- evitar excesso de objetos;
- evitar composição artificial;
- preservar espaço visual e equilíbrio;
- nenhuma moldura ou borda.

NÃO INCLUIR:

- textos;
- títulos;
- letras;
- palavras;
- números;
- logotipos;
- marcas comerciais;
- marcas-d'água visíveis;
- preços;
- etiquetas;
- interfaces;
- banners;
- montagens;
- colagens;
- ilustrações;
- desenhos;
- aparência CGI;
- aparência 3D artificial;
- objetos deformados;
- arquitetura impossível.

A imagem final deve parecer uma fotografia
real feita profissionalmente para um blog
de Casa e Decoração.
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
    para gerar a imagem destacada.
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
    Detecta erros de cota ou limite.
    """

    texto = str(erro).lower()

    termos = (
        "429",
        "resource_exhausted",
        "quota",
        "rate limit",
        "rate_limit",
    )

    return any(
        termo in texto
        for termo in termos
    )


def erro_temporario(erro):
    """
    Detecta erros temporários que
    podem justificar nova tentativa.
    """

    texto = str(erro).lower()

    termos = (
        "503",
        "unavailable",
        "temporarily unavailable",
        "internal error",
        "500",
    )

    return any(
        termo in texto
        for termo in termos
    )


# ============================================================
# EXTRAÇÃO DA IMAGEM
# ============================================================

def extrair_bytes_imagem(interaction):
    """
    Extrai os bytes da imagem retornada
    pela API Gemini.
    """

    output_image = getattr(
        interaction,
        "output_image",
        None,
    )

    if output_image is None:
        raise RuntimeError(
            "A resposta do modelo não "
            "contém uma imagem."
        )

    dados = getattr(
        output_image,
        "data",
        None,
    )

    if not dados:
        raise RuntimeError(
            "A imagem retornada não "
            "possui dados."
        )

    if isinstance(dados, bytes):
        return dados

    if isinstance(dados, str):
        return base64.b64decode(dados)

    raise RuntimeError(
        "Formato de imagem retornado "
        "pela API não reconhecido."
    )


# ============================================================
# GERAÇÃO COM UM MODELO
# ============================================================

def gerar_com_modelo(
    client,
    modelo,
    prompt,
):
    """
    Solicita uma imagem ao Gemini usando
    a Generate Content API.
    """

    print(
        f"Enviando solicitação para {modelo}...",
        flush=True,
    )

    response = client.models.generate_content(
        model=modelo,
        contents=[prompt],
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            response_format={
                "image": {
                    "aspect_ratio": FORMATO_IMAGEM,
                    "image_size": RESOLUCAO_IMAGEM,
                }
            },
        ),
    )

    print(
        "Resposta recebida da API.",
        flush=True,
    )

    for part in response.parts:
        imagem = part.as_image()

        if imagem is not None:
            dados = getattr(
                imagem,
                "image_bytes",
                None,
            )

            if dados:
                return dados

    raise RuntimeError(
        "A API respondeu, mas nenhuma "
        "imagem foi encontrada."
    )


# ============================================================
# GERAÇÃO COM FALLBACK
# ============================================================

def gerar_imagem_destacada(
    titulo,
    palavra_chave,
    categoria="Casa e Decoração",
    pasta_saida=None,
):
    """
    Gera a imagem destacada utilizando
    uma fila de modelos.

    Se um modelo falhar, tenta o próximo.

    Se todos falharem, retorna um resultado
    seguro em vez de derrubar a automação.
    """

    api_key = os.getenv("GEMINI_API_KEY")

    dados = preparar_imagem(
        titulo=titulo,
        palavra_chave=palavra_chave,
        categoria=categoria,
    )

    if not api_key:
        return {
            **dados,
            "gerada": False,
            "modelo": None,
            "caminho": None,
            "erro": (
                "GEMINI_API_KEY não encontrada."
            ),
        }

    if pasta_saida is None:
        pasta_saida = PASTA_IMAGENS
    else:
        pasta_saida = Path(pasta_saida)

    pasta_saida.mkdir(
        parents=True,
        exist_ok=True,
    )

    caminho = (
        pasta_saida
        / dados["nome_arquivo"]
    )

    client = genai.Client(
    api_key=api_key,
    http_options=types.HttpOptions(
        timeout=90000,
        retry_options=types.HttpRetryOptions(
            attempts=1,
        ),
    ),
)

    ultimo_erro = None

    print()
    print(
        "=== GERAÇÃO DE IMAGEM DESTACADA ==="
    )
    print("Arquivo:", dados["nome_arquivo"])
    print("Formato:", dados["formato"])
    print("Resolução:", dados["resolucao"])
    print()

    for modelo in MODELOS_IMAGEM:

        print(
            f"Tentando modelo de imagem: "
            f"{modelo}"
        )

        tentativas = 3

        for tentativa in range(
            1,
            tentativas + 1,
        ):

            try:
                bytes_imagem = (
                    gerar_com_modelo(
                        client=client,
                        modelo=modelo,
                        prompt=dados["prompt"],
                    )
                )

                with open(
                    caminho,
                    "wb",
                ) as arquivo:
                    arquivo.write(
                        bytes_imagem
                    )

                tamanho = caminho.stat().st_size

                if tamanho <= 0:
                    raise RuntimeError(
                        "O arquivo de imagem "
                        "foi criado vazio."
                    )

                print()
                print(
                    "Imagem gerada com sucesso."
                )
                print("Modelo:", modelo)
                print("Caminho:", caminho)
                print(
                    "Tamanho:",
                    f"{tamanho} bytes",
                )

                return {
                    **dados,
                    "gerada": True,
                    "modelo": modelo,
                    "caminho": str(caminho),
                    "tamanho_bytes": tamanho,
                    "erro": None,
                }

            except Exception as erro:
                ultimo_erro = erro

                print(
                    f"Falha no modelo "
                    f"{modelo} "
                    f"(tentativa "
                    f"{tentativa}/"
                    f"{tentativas}):"
                )
                print(str(erro))

                if erro_de_cota(erro):
                    print(
                        "Cota ou limite "
                        "detectado."
                    )
                    print(
                        "Pulando imediatamente "
                        "para o próximo modelo."
                    )
                    break

                if erro_temporario(erro):
                    if tentativa < tentativas:
                        espera = (
                            5
                            if tentativa == 1
                            else 15
                        )

                        print(
                            "Erro temporário."
                        )
                        print(
                            f"Nova tentativa em "
                            f"{espera} segundos..."
                        )

                        time.sleep(espera)
                        continue

                    print(
                        "Modelo permaneceu "
                        "indisponível."
                    )
                    print(
                        "Tentando o próximo."
                    )
                    break

                print(
                    "Erro não temporário."
                )
                print(
                    "Tentando o próximo modelo."
                )
                break

    print()
    print(
        "Nenhum modelo conseguiu "
        "gerar a imagem."
    )
    print(
        "A automação poderá continuar "
        "sem imagem destacada."
    )

    return {
        **dados,
        "gerada": False,
        "modelo": None,
        "caminho": None,
        "tamanho_bytes": 0,
        "erro": str(ultimo_erro)
        if ultimo_erro
        else "Erro desconhecido.",
    }


# ============================================================
# TESTE ISOLADO
# ============================================================

if __name__ == "__main__":

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
    print("=== RESULTADO DO TESTE ===")
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
        "Caminho:",
        resultado["caminho"],
    )

    if resultado["erro"]:
        print(
            "Erro:",
            resultado["erro"],
        )
