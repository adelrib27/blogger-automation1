import re
import unicodedata


def limpar_texto(texto):
    if not texto:
        return ""

    return re.sub(r"\s+", " ", str(texto)).strip()


def criar_nome_arquivo(titulo):
    """
    Cria um nome de arquivo amigável para SEO.
    Exemplo:
    Como Organizar a Cozinha -> como-organizar-a-cozinha.jpg
    """
    titulo = limpar_texto(titulo).lower()

    titulo = unicodedata.normalize("NFKD", titulo)
    titulo = "".join(
        caractere
        for caractere in titulo
        if not unicodedata.combining(caractere)
    )

    titulo = re.sub(r"[^a-z0-9\s-]", "", titulo)
    titulo = re.sub(r"[\s_-]+", "-", titulo)
    titulo = titulo.strip("-")

    if not titulo:
        titulo = "imagem-destacada"

    return f"{titulo[:80]}.jpg"


def criar_alt_text(titulo, palavra_chave):
    """
    Cria texto alternativo para acessibilidade e SEO.
    """
    titulo = limpar_texto(titulo)
    palavra_chave = limpar_texto(palavra_chave)

    if palavra_chave:
        return f"{titulo} - {palavra_chave}"[:125]

    return titulo[:125]


def criar_prompt_imagem(
    titulo,
    palavra_chave,
    categoria="Casa e Decoração"
):
    """
    Cria o prompt que será enviado posteriormente
    ao gerador de imagens.
    """

    titulo = limpar_texto(titulo)
    palavra_chave = limpar_texto(palavra_chave)
    categoria = limpar_texto(categoria)

    prompt = f"""
Crie uma imagem destacada fotorrealista para um artigo de blog.

Tema do artigo: {titulo}
Palavra-chave principal: {palavra_chave}
Categoria: {categoria}

A imagem deve representar visualmente o assunto principal do artigo.

Estilo:
fotografia editorial de alta qualidade;
ambiente residencial brasileiro moderno e realista;
decoração elegante, acolhedora e acessível;
iluminação natural;
composição limpa;
cores naturais;
objetos e móveis em proporções realistas;
aparência profissional para blog de Casa e Decoração.

Requisitos:
formato horizontal 16:9;
alta resolução;
assunto principal claramente visível;
boa composição para imagem destacada;
sem textos;
sem letras;
sem logotipos;
sem marcas-d'água;
sem preços;
sem elementos de interface;
sem aparência de ilustração ou CGI.
"""

    return limpar_texto(prompt)


def preparar_imagem(titulo, palavra_chave, categoria="Casa e Decoração"):
    """
    Monta todas as informações necessárias
    para gerar a imagem destacada.
    """

    return {
        "nome_arquivo": criar_nome_arquivo(titulo),
        "alt_text": criar_alt_text(titulo, palavra_chave),
        "prompt": criar_prompt_imagem(
            titulo,
            palavra_chave,
            categoria
        ),
        "formato": "16:9",
        "tipo": "imagem_destacada"
    }


if __name__ == "__main__":
    teste = preparar_imagem(
        titulo="Como organizar uma cozinha pequena de forma prática",
        palavra_chave="organização de cozinha pequena"
    )

    print("Módulo de imagem iniciado com sucesso.")
    print("Arquivo:", teste["nome_arquivo"])
    print("ALT:", teste["alt_text"])
    print("Formato:", teste["formato"])
    print("Prompt:", teste["prompt"])
