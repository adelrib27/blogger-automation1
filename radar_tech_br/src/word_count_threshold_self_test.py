from quality_gate import MAX_WORDS, MIN_WORDS, quality

assert MIN_WORDS == 700, f"MIN_WORDS esperado=700, recebido={MIN_WORDS}"
assert MAX_WORDS == 1400, f"MAX_WORDS esperado=1400, recebido={MAX_WORDS}"

def reasons_for(count):
    words = " ".join(["palavra"] * count)
    editorial = (
        "<h2>Contexto inicial</h2><p>" + words + "</p>"
        "<h2>Critérios de escolha</h2><p>Conteúdo editorial.</p>"
        "<h2>Limitações importantes</h2><p>Conteúdo editorial.</p>"
        "<h2>Conclusão prática</h2><p>Conteúdo editorial.</p>"
    )
    result = quality({
        "editorial_html": editorial,
        "content_html": editorial,
        "word_count": count,
        "seo_title": "Guia de escolha",
        "focus_keyword": "guia de escolha",
        "category": "Tecnologia",
        "product": "produto de referência",
    })
    return result.get("reasons", [])

assert not any(r.startswith("word_count_baixo:") for r in reasons_for(700)), "700 palavras não pode falhar no mínimo"
assert any(r == "word_count_baixo:699" for r in reasons_for(699)), "699 palavras deve falhar no mínimo"
assert not any(r.startswith("word_count_alto:") for r in reasons_for(1400)), "1400 palavras não pode falhar no máximo"
assert any(r == "word_count_alto:1401" for r in reasons_for(1401)), "1401 palavras deve falhar no máximo"
print("Word-count threshold self-test: 4/4 OK (699 bloqueado; 700 aceito; 1400 aceito; 1401 bloqueado).")
