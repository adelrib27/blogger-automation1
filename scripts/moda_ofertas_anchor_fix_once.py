from pathlib import Path

path = Path("blogger_stores/src/moda_ofertas_store.py")
raw = path.read_text(encoding="utf-8")

pairs = [
    ('    ("#bls-casa-organizacao", "#bls-moda-feminina"),', '    (\'href="#bls-casa-organizacao"\', \'href="#bls-moda-feminina"\'),'),
    ('    ("#bls-cozinha-utilidades", "#bls-moda-masculina"),', '    (\'href="#bls-cozinha-utilidades"\', \'href="#bls-moda-masculina"\'),'),
    ('    ("#bls-tecnologia", "#bls-calcados-bolsas"),', '    (\'href="#bls-tecnologia"\', \'href="#bls-calcados-bolsas"\'),'),
    ('    ("#bls-beleza", "#bls-acessorios"),', '    (\'href="#bls-beleza"\', \'href="#bls-acessorios"\'),'),
    ('    ("#bls-dia-a-dia", "#bls-beleza-cuidados"),', '    (\'href="#bls-dia-a-dia"\', \'href="#bls-beleza-cuidados"\'),'),
]

for old, new in pairs:
    if old not in raw:
        raise SystemExit(f"Âncora antiga não encontrada; abortando fail-closed: {old}")
    raw = raw.replace(old, new, 1)

needle = """    # Normalizações idempotentes: preservam a categoria final de beleza e
    # mantêm texto/âncora dos CTAs do hero semanticamente alinhados.
"""
insert = """    # Normalizações idempotentes: preservam a categoria final de beleza e
    # mantêm texto/âncora dos CTAs do hero semanticamente alinhados.
    # Recupera qualquer valor composto gerado por uma versão antiga que usava
    # substituição por prefixo em #bls-beleza.
    out = out.replace('#bls-acessorios-cuidados', '#bls-beleza-cuidados')
"""
if needle not in raw:
    raise SystemExit("Bloco de normalização não encontrado; abortando fail-closed.")
raw = raw.replace(needle, insert, 1)

path.write_text(raw, encoding="utf-8")
print("MODA_OFERTAS_ANCHOR_SOURCE_FIX_READY")
