import re


FIXER_WORDS = r"(?:parafusos?|pregos?|porcas?|arruelas?|buchas?)"

FREQUENCY_REPLACEMENTS = (
    (
        re.compile(
            r"\b(?:ferramentas?|itens?|objetos?|fixadores?)\s+(?:de\s+)?uso\s+(?:mais\s+)?frequente\b",
            re.I,
        ),
        "itens que você identifica como mais acessados na sua rotina",
    ),
    (
        re.compile(
            r"\b(?:ferramentas?|itens?|objetos?|fixadores?)\s+(?:que\s+)?(?:são\s+)?(?:usados?|utilizados?)\s+com\s+mais\s+(?:frequência|regularidade)\b",
            re.I,
        ),
        "itens que você identifica como mais acessados na sua rotina",
    ),
    (
        re.compile(
            r"\b(?:ferramentas?|itens?|objetos?|fixadores?)\s+que\s+(?:você\s+)?(?:usa|utiliza)\s+com\s+(?:mais\s+)?(?:frequência|regularidade)\b",
            re.I,
        ),
        "itens que você identifica como mais acessados na sua rotina",
    ),
    (
        re.compile(
            r"\b(?:ferramentas?|itens?|objetos?|fixadores?)\s+(?:que\s+)?(?:são\s+)?(?:usados?|utilizados?)\s+(?:diariamente|todos\s+os\s+dias)\b",
            re.I,
        ),
        "itens que você identifica como mais acessados na sua rotina",
    ),
    (
        re.compile(
            r"\b(?:ferramentas?|itens?|objetos?|fixadores?)\s+(?:que\s+)?(?:são\s+)?(?:usados?|utilizados?)\s+com\s+menos\s+frequência\b",
            re.I,
        ),
        "outros itens",
    ),
    (
        re.compile(r"\b(?:as|os)\s+que\s+(?:são\s+)?(?:usadas?|usados?|utilizadas?|utilizados?)\s+com\s+menos\s+frequência\b", re.I),
        "outros itens",
    ),
    (
        re.compile(r"\b(?:itens?|ferramentas?|objetos?)\s+menos\s+(?:usados?|utilizados?)\b", re.I),
        "outros itens",
    ),
    (
        re.compile(r"\b(?:mais\s+)?frequentemente\s+(?:usados?|utilizados?)\b", re.I),
        "mais acessados na sua rotina",
    ),
    (re.compile(r"\buso\s+di[aá]rio\b", re.I), "uso"),
    (re.compile(r"\b(?:pequenas\s+)?a[cç][oõ]es\s+di[aá]rias\b", re.I), "ações simples"),
    (re.compile(r"\bcom\s+certa\s+frequ[eê]ncia\b", re.I), "periodicamente"),
    (re.compile(r"\bfrequ[eê]ncia\s+de\s+uso\b", re.I), "necessidade de acesso"),
)

ABSOLUTE_SENTENCE_PATTERNS = (
    re.compile(r"\bgarant(?:e|ir|indo|ido)\b.*\bsempre\b", re.I),
    re.compile(r"\bprote[cç][aã]o\s+garantida\b", re.I),
    re.compile(r"\b100\s*%\s+(?:seguro|protegido|garantido)\b", re.I),
    re.compile(r"\bpreservar\s+a\s+qualidade\b", re.I),
    re.compile(r"\bevitar?\s+acidentes?\b", re.I),
)


def _normalize_headings(value):
    value = re.sub(
        r"<h2\b[^>]*>[^<]*(?:frequ[eê]ncia\s+de\s+uso|uso\s+di[aá]rio)[^<]*</h2>",
        "<h2>Organize por tipo de item e necessidade de acesso</h2>",
        value,
        flags=re.I,
    )
    value = re.sub(
        r"<h2\b[^>]*>[^<]*a[cç][oõ]es\s+di[aá]rias[^<]*</h2>",
        "<h2>Mantenha a organização com ações simples</h2>",
        value,
        flags=re.I,
    )
    return value


def _normalize_classification(value):
    value = re.sub(
        rf"\bferramentas?(?:\s+(?:pequenas?|menores?))?,\s+como\s+({FIXER_WORDS}(?:\s*,\s*{FIXER_WORDS})*(?:\s+e\s+{FIXER_WORDS})?)",
        r"fixadores, como \1",
        value,
        flags=re.I,
    )
    value = re.sub(
        rf"\bmateriais?,\s+como\s+({FIXER_WORDS}(?:\s*,\s*{FIXER_WORDS})*(?:\s+e\s+{FIXER_WORDS})?)",
        r"fixadores, como \1",
        value,
        flags=re.I,
    )
    return value


def _drop_absolute_sentences(paragraph_html):
    open_match = re.match(r"(<p\b[^>]*>)", paragraph_html, flags=re.I)
    close_match = re.search(r"(</p>)\s*$", paragraph_html, flags=re.I)
    if not open_match or not close_match:
        return paragraph_html

    opening = open_match.group(1)
    body = paragraph_html[open_match.end() : close_match.start()].strip()
    sentences = re.split(r"(?<=[.!?])\s+", body)
    kept = []
    for sentence in sentences:
        if any(pattern.search(sentence) for pattern in ABSOLUTE_SENTENCE_PATTERNS):
            continue
        kept.append(sentence.strip())
    body = " ".join(x for x in kept if x).strip()
    return f"{opening}{body}</p>" if body else ""


def normalize_editorial(value):
    value = str(value or "").strip()
    value = _normalize_headings(value)
    value = _normalize_classification(value)

    for pattern, replacement in FREQUENCY_REPLACEMENTS:
        value = pattern.sub(replacement, value)

    value = re.sub(
        r"<p\b[^>]*>.*?</p>",
        lambda match: _drop_absolute_sentences(match.group(0)),
        value,
        flags=re.I | re.S,
    )
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()
