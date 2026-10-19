import re


def normalize_editorial(value):
    """Normalização conservadora: corrige apenas artefatos estruturais, sem inventar conteúdo."""
    text = str(value or "").strip()
    text = re.sub(r"</?(?:html|head|body)[^>]*>", "", text, flags=re.I)
    text = re.sub(r"<h1\b[^>]*>.*?</h1>", "", text, flags=re.I | re.S)
    text = re.sub(r"<p\b[^>]*>\s*</p>", "", text, flags=re.I)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n[ \t]+", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


if __name__ == "__main__":
    sample = "<body><h1>Título</h1>\n<p> Texto   útil. </p>\n\n\n<h2>Seção</h2></body>"
    out = normalize_editorial(sample)
    assert "<h1" not in out and "<body" not in out and "<h2>Seção</h2>" in out
    print("Normalizer Casa e Decoração: OK")
