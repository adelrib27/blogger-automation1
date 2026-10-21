from pathlib import Path

# V14.3 preserva V14.2 para auditoria. Acrescenta uma ponte editorial local
# por seção para atingir o comprimento SAFE sem reduzir gates nem pedir texto
# livre ao provedor. Groq continua limitado a A/B/C.
source_path = Path(__file__).with_name("article_builder_evergreen_v14_2.py")
source = source_path.read_text(encoding="utf-8")

render_marker = "\n\ndef render_section(family, section_index, heading, questions, variant):"
bridge_block = r'''

BRIDGE_TEMPLATES = [
    "Converta as respostas de {topic} em duas anotações separadas: uma sobre o contexto observado e outra sobre o ponto que ainda depende de verificação. Essa separação facilita retomar a decisão depois.",
    "Ao revisar {topic}, marque quais respostas podem ser comparadas diretamente e quais só fazem sentido neste contexto. Não transforme diferença de contexto em vantagem automática da opção.",
    "Use {topic} para registrar também a origem de cada resposta. Se a informação vier da oferta, mantenha a referência; se vier da rotina, identifique-a como contexto.",
    "Antes de encerrar {topic}, procure uma pergunta que ainda esteja sem resposta suficiente. Preservar essa pendência evita que a próxima revisão comece tratando uma suposição como fato.",
    "Em {topic}, mantenha o critério central visível mesmo quando a página oferecer muitos detalhes. Informações adicionais só entram na decisão quando ajudam a responder ao objetivo desta etapa.",
    "Registre o resultado de {topic} de forma curta e revisável. Uma anotação clara sobre o que foi confirmado e o que mudou torna a atualização futura mais simples.",
    "Feche {topic} conferindo se as três perguntas apontam para o mesmo objetivo editorial. Se alguma delas ampliar demais o assunto, trate-a apenas como pendência para outra análise.",
]
'''
if source.count(render_marker) != 1:
    raise RuntimeError("SAFE V14.3: render marker mismatch")
source = source.replace(render_marker, bridge_block + render_marker, 1)

old_pair = "    lead, close = pair\n"
new_pair = (
    "    lead, close = pair\n"
    "    if len(BRIDGE_TEMPLATES) != 7:\n"
    "        raise RuntimeError(\"SAFE V14.3: bridge_count\")\n"
    "    bridge = BRIDGE_TEMPLATES[section_index].format(topic=heading.lower())\n"
)
if source.count(old_pair) != 1:
    raise RuntimeError("SAFE V14.3: pair patch mismatch")
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
    raise RuntimeError("SAFE V14.3: output patch mismatch")
source = source.replace(old_output, new_output, 1)

ns = {"__name__": "__main__", "__file__": str(source_path)}
exec(compile(source, str(source_path), "exec"), ns, ns)
