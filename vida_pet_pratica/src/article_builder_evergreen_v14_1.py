from pathlib import Path

# V14.1 é um hotfix estritamente técnico do V14.
# O V14 executa o V13 em namespace isolado; nesse encadeamento,
# safety_check_editorial permanece no namespace V9 aninhado em ns["ns"].
# Nenhum template, gate, threshold ou regra editorial é alterado aqui.
source_path = Path(__file__).with_name("article_builder_evergreen_v14.py")
source = source_path.read_text(encoding="utf-8")
old = '    ns["safety_check_editorial"](html)\n'
new = '    ns["ns"]["safety_check_editorial"](html)\n'
if source.count(old) != 1:
    raise RuntimeError("SAFE V14.1: ponto único de hotfix V14 não encontrado")
source = source.replace(old, new, 1)
exec(compile(source, str(source_path), "exec"), {"__name__": "__main__", "__file__": str(source_path)})
