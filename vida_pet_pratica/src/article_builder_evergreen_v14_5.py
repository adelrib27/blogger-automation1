from pathlib import Path

# V14.5 preserva V14.4 para auditoria. A única mudança é de roteamento editorial:
# ângulos explícitos de critérios para escolher atividades deixam de compartilhar
# a família "routine" com ângulos de interação. Isso reduz colisão semântica por
# diversidade estrutural, sem reduzir threshold, gate factual ou regra SAFE.
source_path = Path(__file__).with_name("article_builder_evergreen_v14_4.py")
source = source_path.read_text(encoding="utf-8")

old_marker = 'def family_for(candidate):\n    angle = evidence.normalize(candidate.get("angle") or "")\n'
new_marker = (
    'def family_for(candidate):\n'
    '    angle = evidence.normalize(candidate.get("angle") or "")\n'
    '    if "criterios" in angle and "atividade" in angle:\n'
    '        return "comparison"\n'
)
if source.count(old_marker) != 1:
    raise RuntimeError("SAFE V14.5: family_for marker mismatch")
source = source.replace(old_marker, new_marker, 1)

ns = {"__name__": "__main__", "__file__": str(source_path)}
exec(compile(source, str(source_path), "exec"), ns, ns)
