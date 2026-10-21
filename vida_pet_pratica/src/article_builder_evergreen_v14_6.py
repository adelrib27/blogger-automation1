from pathlib import Path

# V14.6 preserva V14.2/V14.4/V14.5 para auditoria.
# Corrige apenas o ponto de aplicação da diversidade estrutural: V14.2 carrega
# V14 em runtime, então o family_for deve ser ajustado nesse source interno.
# Também preserva a ponte editorial curta de V14.4.
# Nenhum threshold, gate factual, regra SAFE ou política de evidência é reduzido.
source_path = Path(__file__).with_name("article_builder_evergreen_v14_2.py")
source = source_path.read_text(encoding="utf-8")

load_marker = 'source = source_path.read_text(encoding="utf-8")\n\nold_namespace = '
load_replacement = '''source = source_path.read_text(encoding="utf-8")

family_marker = 'def family_for(candidate):\\n    angle = evidence.normalize(candidate.get("angle") or "")\\n'
family_replacement = (
    'def family_for(candidate):\\n'
    '    angle = evidence.normalize(candidate.get("angle") or "")\\n'
    '    if "criterios" in angle and "atividade" in angle:\\n'
    '        return "comparison"\\n'
)
if source.count(family_marker) != 1:
    raise RuntimeError("SAFE V14.6: family_for inner marker mismatch")
source = source.replace(family_marker, family_replacement, 1)

old_namespace = '''
if source.count(load_marker) != 1:
    raise RuntimeError("SAFE V14.6: V14.2 load marker mismatch")
source = source.replace(load_marker, load_replacement, 1)

render_marker = "\n\ndef render_section(family, section_index, heading, questions, variant):"
bridge_block = r'''

BRIDGE_TEMPLATES = [
    "Em {topic}, separe contexto de pendências que ainda exigem consulta à fonte correta.",
    "Ao revisar {topic}, registre qual resposta realmente muda a decisão.",
    "Use {topic} para anotar a origem de cada resposta antes da comparação.",
    "Antes de encerrar {topic}, mantenha visível qualquer dúvida ainda aberta.",
    "Em {topic}, preserve o critério principal e descarte detalhes sem função.",
    "Registre {topic} distinguindo observação de informação que ainda precisa ser confirmada.",
    "Feche {topic} verificando se as perguntas continuam ligadas ao objetivo editorial.",
]
'''
if source.count(render_marker) != 1:
    raise RuntimeError("SAFE V14.6: render marker mismatch")
source = source.replace(render_marker, bridge_block + render_marker, 1)

old_pair = "    lead, close = pair\n"
new_pair = (
    "    lead, close = pair\n"
    "    if len(BRIDGE_TEMPLATES) != 7:\n"
    "        raise RuntimeError(\"SAFE V14.6: bridge_count\")\n"
    "    bridge = BRIDGE_TEMPLATES[section_index].format(topic=heading.lower())\n"
)
if source.count(old_pair) != 1:
    raise RuntimeError("SAFE V14.6: pair patch mismatch")
source = source.replace(old_pair, new_pair, 1)

old_output = (
    '        f"{question_html}"\n'
    '        f"<p>{escape(close)}</p>"\n'
)
new_output = (
    '        f"{question_html}"\n'
    '        f"<p>{escape(bridge)}</p>"\n'
    '        f"<p>{escape(close)}</p>"\n'
)
if source.count(old_output) != 1:
    raise RuntimeError("SAFE V14.6: output patch mismatch")
source = source.replace(old_output, new_output, 1)

ns = {"__name__": "__main__", "__file__": str(source_path)}
exec(compile(source, str(source_path), "exec"), ns, ns)
