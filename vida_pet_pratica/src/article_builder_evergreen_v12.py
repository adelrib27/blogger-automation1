import hashlib
import re
import time
from html import escape
from pathlib import Path

import article_builder_v1 as builder
import evidence_engine as evidence

# V12 usa uma única geração do Groq por candidato. O rascunho é saneado e,
# quando necessário, completado localmente com blocos editoriais neutros e
# variados. Gates, evidências e injeção determinística de fatos permanecem V9.
source_path = Path(__file__).with_name("article_builder_evergreen_v9.py")
source = source_path.read_text(encoding="utf-8")
marker = "\nbuilder.main()\n"
if marker not in source:
    raise RuntimeError("SAFE V12: ponto de entrada V9 não encontrado")
source = source.rsplit(marker, 1)[0] + "\n"
ns = {"__name__": "vida_pet_evergreen_v9_for_v12", "__file__": str(source_path)}
exec(compile(source, str(source_path), "exec"), ns, ns)

original_call = ns["original_call"]
base_prompt = ns["editorial_prompt"]
sanitize_html = ns["sanitize_html"]
safety_check_editorial = ns["safety_check_editorial"]
normalize_doc = ns["normalize_doc"]
strict_gate = ns["strict_gate"]
current_candidate = ns["current_candidate"]
current_package = ns["current_package"]
SPEC_TERMS = ns["SPEC_TERMS"]
ABSOLUTE_PATTERNS = ns["ABSOLUTE_PATTERNS"]

TARGET_WORDS = 650
MIN_ORIGINAL_WORDS = 360
MAX_LOCAL_ADDED_WORDS = 290
MIN_CALL_INTERVAL_SECONDS = 18.0
LAST_CALL = [0.0]

SAFE_HEADINGS = [
    ["Comece pela pergunta principal", "Organize a decisão antes de comparar", "Defina o foco desta análise"],
    ["Separe contexto e fonte", "Observe o cenário antes de concluir", "Registre o que depende do contexto"],
    ["Transforme dúvidas em verificações", "Converta dúvidas em perguntas úteis", "Liste o que ainda precisa de consulta"],
    ["Compare sem preencher lacunas", "Mantenha pendências visíveis", "Evite concluir além das fontes"],
    ["Revise a página atual do item", "Volte às fontes antes da escolha", "Confira o que pode ter mudado"],
    ["Organize as anotações da decisão", "Registre critérios e pendências", "Guarde uma trilha simples da análise"],
    ["Feche a análise com clareza", "Revise os pontos antes de decidir", "Finalize sem transformar dúvida em certeza"],
]

FILLERS = [
    "Antes de concluir esta etapa, transforme as dúvidas em perguntas curtas e verificáveis. Separe o que depende do ambiente, o que depende da rotina e o que só pode ser confirmado na página atual do item.",
    "Registre também o que ainda ficou aberto. Uma pendência explícita ajuda a comparar alternativas sem preencher lacunas por suposição e deixa claro quais pontos merecem nova consulta antes da decisão.",
    "Observe o contexto de uso sem tentar antecipar uma resposta. Anotar onde a escolha será feita, quem participa da rotina e quais limitações existem ajuda a formular perguntas mais úteis para a consulta.",
    "Ao rever as fontes, diferencie informação atual de impressão pessoal. O objetivo desta etapa é saber o que pode ser conferido agora e o que deve continuar marcado como dúvida até surgir uma referência adequada.",
    "Uma comparação fica mais clara quando cada critério responde a uma pergunta concreta. Em vez de acumular descrições, registre por que determinado ponto importa para a rotina e onde a resposta poderá ser verificada.",
    "Se duas referências parecerem apontar em direções diferentes, mantenha a questão aberta. Voltar à página ligada ao item e procurar uma explicação mais direta é preferível a escolher a interpretação mais conveniente.",
    "Também vale separar necessidade de preferência. A necessidade orienta o que precisa ser conferido; a preferência ajuda a ordenar alternativas depois. Essa distinção evita transformar gosto pessoal em conclusão sobre o item.",
    "Faça uma revisão curta das anotações antes de avançar. Perguntas repetidas podem ser reunidas, enquanto dúvidas realmente diferentes devem permanecer separadas para que nenhuma resposta seja aplicada ao ponto errado.",
    "Quando uma informação não estiver disponível, registre a ausência de forma simples. Isso preserva a qualidade da comparação e facilita uma nova consulta sem obrigar o leitor a reconstruir todo o raciocínio.",
    "Procure manter o foco no ângulo desta página. Se surgir uma dúvida interessante, mas distante do objetivo atual, anote para outra pesquisa em vez de desviar a análise e repetir assuntos já tratados.",
    "A etapa seguinte pode começar pelas fontes que têm relação mais direta com o item. Referências gerais ajudam a formular perguntas, mas a decisão sobre um detalhe específico deve permanecer ligada à fonte correspondente.",
    "Organizar a consulta por temas evita saltos entre assuntos. Agrupe perguntas próximas, revise cada grupo e marque o que foi respondido, o que mudou e o que ainda depende de uma checagem posterior.",
    "Evite usar a quantidade de informações como sinal de qualidade. Uma resposta curta, mas ligada à fonte correta, pode ser mais útil do que várias descrições que não deixam claro a qual item se referem.",
    "Ao comparar alternativas, use o mesmo conjunto de perguntas sempre que possível. Isso ajuda a perceber diferenças de informação sem transformar a análise em uma sequência de impressões difíceis de revisar.",
    "Reserve um momento para verificar se alguma conclusão surgiu apenas da imagem, do título ou de uma palavra promocional. Quando isso acontecer, converta a impressão em pergunta e procure uma fonte que possa esclarecê-la.",
    "Uma boa anotação explica por que o ponto foi considerado, sem tentar encerrar a questão cedo demais. Esse hábito torna a escolha mais fácil de revisar quando a página do item ou o contexto da rotina muda.",
    "Se o ambiente tiver mais de uma possibilidade, mantenha alternativas abertas durante a pesquisa. Comparar cenários ajuda a identificar quais perguntas realmente fazem diferença antes de escolher um caminho.",
    "No fim desta parte, releia as dúvidas como se outra pessoa fosse continuar a pesquisa. Perguntas claras e pendências bem marcadas reduzem ambiguidades e tornam a próxima consulta mais objetiva.",
    "Considere registrar a origem de cada resposta junto da própria anotação. Assim, fica mais simples voltar à referência certa quando um detalhe precisar ser revisto, sem misturar informações de páginas diferentes.",
    "Em vez de buscar uma conclusão geral, avance por decisões pequenas. Confirmar uma questão de cada vez deixa o raciocínio visível e reduz a chance de uma suposição passar a ser tratada como informação estabelecida.",
    "Se uma expressão parecer vaga, reescreva a dúvida em linguagem comum. Perguntas simples sobre uso, rotina, consulta e contexto costumam produzir uma análise mais clara do que repetir termos promocionais.",
    "Antes de encerrar, confira se as perguntas desta seção ainda correspondem ao objetivo do artigo. Remover desvios ajuda a preservar uma abordagem própria e evita que o texto repita estruturas usadas em outras páginas.",
    "A pesquisa pode terminar com pontos em aberto sem perder utilidade. Mostrar o que ainda precisa de consulta ajuda o leitor a decidir quais informações são essenciais e quais podem ser verificadas em outro momento.",
    "Quando houver várias páginas disponíveis, comece pela que identifica melhor o item e use as demais apenas como apoio de contexto. Essa ordem mantém a análise organizada e reduz associações indevidas.",
    "Anote mudanças percebidas entre consultas sem apagar o registro anterior. Uma trilha simples ajuda a entender o que merece nova atenção e evita tratar informação antiga como se ainda estivesse confirmada.",
    "Procure formular critérios que possam ser revisitados. Uma pergunta bem definida continua útil mesmo quando a oferta muda, porque orienta a nova consulta sem depender de uma descrição específica do anúncio.",
    "Ao finalizar a seção, resuma mentalmente o que foi confirmado e o que permanece pendente. Se essa separação não estiver clara, retorne às anotações antes de seguir para a próxima parte da análise.",
    "Mantenha cada conclusão proporcional à fonte disponível. Quando a referência responde apenas parte da pergunta, registre apenas essa parte e deixe o restante aberto para uma checagem futura.",
]

OUTCOME_PATTERN = re.compile(
    r"\b(?:reduz|elimina|previne|cura|melhora|acalma|estimula)\s+"
    r"(?:ansiedade|estresse|dor|doenca|sintoma|comportamento)\b"
)


def unsafe_plain(text):
    plain = re.sub(r"\s+", " ", str(text or "")).strip()
    if not plain:
        return False
    if re.search(r"\d", plain):
        return True
    norm = evidence.normalize(plain)
    for term in SPEC_TERMS:
        term_norm = evidence.normalize(term)
        if term_norm and re.search(rf"(?<!\w){re.escape(term_norm)}(?!\w)", norm):
            return True
    if any(re.search(pattern, norm) for pattern in ABSOLUTE_PATTERNS):
        return True
    if OUTCOME_PATTERN.search(norm):
        return True
    return False


def safe_text_sentences(text):
    plain = re.sub(r"\s+", " ", builder.html_text(text)).strip()
    if not plain:
        return ""
    parts = re.split(r"(?<=[.!?])\s+", plain)
    kept = [part.strip() for part in parts if part.strip() and not unsafe_plain(part)]
    return " ".join(kept).strip()


def heading_for(candidate, section_index):
    seed = f"{candidate.get('itemId') or ''}|{candidate.get('angle') or ''}|heading|{section_index}"
    options = SAFE_HEADINGS[section_index % len(SAFE_HEADINGS)]
    pick = int(hashlib.sha256(seed.encode("utf-8")).hexdigest()[:8], 16) % len(options)
    return options[pick]


def clean_body(body):
    cleaned = []
    for block in re.findall(r"<p>.*?</p>|<h3>.*?</h3>|<ul>.*?</ul>", body, flags=re.I | re.S):
        lower = block.lstrip().lower()
        if lower.startswith("<ul>"):
            items = []
            for li in re.findall(r"<li>.*?</li>", block, flags=re.I | re.S):
                safe = safe_text_sentences(li)
                if safe:
                    items.append(f"<li>{escape(safe)}</li>")
            if items:
                cleaned.append("<ul>" + "".join(items) + "</ul>")
            continue
        tag = "h3" if lower.startswith("<h3>") else "p"
        safe = safe_text_sentences(block)
        if safe and not unsafe_plain(safe):
            cleaned.append(f"<{tag}>{escape(safe)}</{tag}>")
    return cleaned


def parse_sections(html, candidate):
    clean = sanitize_html(html)
    pattern = re.compile(r"<h2>(.*?)</h2>(.*?)(?=<h2>|$)", flags=re.I | re.S)
    matches = list(pattern.finditer(clean))
    if len(matches) != 7:
        raise RuntimeError(f"SAFE V12 local repair: h2_count:{len(matches)}")
    prefix = clean[:matches[0].start()]
    sections = []
    for idx, match in enumerate(matches):
        heading = safe_text_sentences(match.group(1))
        if not heading or unsafe_plain(heading):
            heading = heading_for(candidate, idx)
        body = (prefix if idx == 0 else "") + match.group(2)
        sections.append([heading, clean_body(body)])
    return sections


def render_sections(sections):
    return "".join(
        f"<h2>{escape(heading)}</h2>" + "".join(blocks)
        for heading, blocks in sections
    )


def filler_order(candidate):
    base = f"{candidate.get('itemId') or ''}|{candidate.get('angle') or ''}|local-fill"
    ranked = []
    for idx, text in enumerate(FILLERS):
        digest = hashlib.sha256(f"{base}|{idx}".encode("utf-8")).hexdigest()
        ranked.append((digest, idx, text))
    ranked.sort()
    return [(idx, text) for _, idx, text in ranked]


def local_repair_editorial(raw_html, candidate):
    sections = parse_sections(raw_html, candidate)
    repaired = render_sections(sections)
    original_wc = builder.word_count(repaired)
    if original_wc < MIN_ORIGINAL_WORDS:
        raise RuntimeError(f"SAFE V12 local repair: original_too_short:{original_wc}")
    if original_wc > 780:
        raise RuntimeError(f"SAFE V12 local repair: original_too_long:{original_wc}")

    added_before = original_wc
    if original_wc < TARGET_WORDS:
        order = filler_order(candidate)
        cursor = 0
        section_cursor = 0
        while builder.word_count(render_sections(sections)) < TARGET_WORDS and cursor < len(order):
            _, text = order[cursor]
            cursor += 1
            if unsafe_plain(text):
                continue
            section_index = section_cursor % len(sections)
            sections[section_index][1].append(f"<p>{escape(text)}</p>")
            section_cursor += 1
            current = render_sections(sections)
            added = builder.word_count(current) - added_before
            if added > MAX_LOCAL_ADDED_WORDS or builder.word_count(current) > 760:
                sections[section_index][1].pop()
                break

    repaired = render_sections(sections)
    final_wc = builder.word_count(repaired)
    if final_wc < 580:
        raise RuntimeError(f"SAFE V12 local repair: still_too_short:{final_wc}")
    if final_wc > 780:
        raise RuntimeError(f"SAFE V12 local repair: too_long:{final_wc}")
    safety_check_editorial(repaired)
    return repaired


def editorial_call(prompt):
    elapsed = time.monotonic() - LAST_CALL[0]
    if LAST_CALL[0] and elapsed < MIN_CALL_INTERVAL_SECONDS:
        time.sleep(MIN_CALL_INTERVAL_SECONDS - elapsed)
    LAST_CALL[0] = time.monotonic()
    raw, usage = original_call(prompt)
    if not isinstance(raw, dict):
        raise RuntimeError("SAFE V12: resposta editorial não é objeto JSON")
    repaired = local_repair_editorial(raw.get("article_html") or "", current_candidate[0])
    safe_raw = dict(raw)
    safe_raw["article_html"] = repaired
    return normalize_doc(safe_raw, current_candidate[0], current_package[0]), usage


builder.prompt_for = base_prompt
builder.groq_call = editorial_call
builder.gate = strict_gate
builder.main()
