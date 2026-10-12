import html
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
FILA_PATH = BASE_DIR / "data" / "facebook_fila_grupos.json"
HISTORICO_PATH = BASE_DIR / "data" / "facebook_grupos_publicados.json"
SAIDA_PATH = BASE_DIR / "artifacts" / "facebook_grupos_painel.html"
ACTIONS_URL = "https://github.com/adelrib27/blogger-automation1/actions/workflows/facebook_grupos_marcar.yml"


def carregar(path):
    if not path.exists():
        return []
    try:
        dados = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    return dados if isinstance(dados, list) else []


def esc(valor):
    return html.escape(str(valor or ""), quote=True)


def card(item):
    grupo = item.get("group") or {}
    post = item.get("post") or {}
    texto = (item.get("copy") or {}).get("text") or ""
    imagem = post.get("featured_image_url") or ""
    queue_id = str(item.get("queue_id") or "")

    botoes = [
        f'<a class="btn" target="_blank" rel="noopener" href="{esc(grupo.get("url"))}">Abrir grupo</a>',
        f'<a class="btn" target="_blank" rel="noopener" href="{esc(post.get("url"))}">Abrir artigo</a>',
    ]
    if imagem:
        botoes.append(f'<a class="btn" target="_blank" rel="noopener" href="{esc(imagem)}">Abrir imagem</a>')
    botoes.append(f'<button class="btn" data-copy="{esc(texto)}" onclick="copyData(this)">Copiar texto</button>')
    botoes.append(f'<button class="btn" data-copy="{esc(queue_id)}" onclick="copyData(this)">Copiar Queue ID</button>')
    botoes.append(f'<button class="btn primary" data-copy="{esc(queue_id)}" onclick="markPublished(this)">Marcar como publicado</button>')

    return f"""
    <article class="card">
      <div class="status">PENDENTE</div>
      <h2>{esc(grupo.get('nome'))}</h2>
      <p class="meta">Queue ID: <code>{esc(queue_id)}</code> · Variação {(item.get('copy') or {}).get('variation', '')}</p>
      <h3>{esc(post.get('title'))}</h3>
      <textarea readonly>{esc(texto)}</textarea>
      <div class="actions">{''.join(botoes)}</div>
    </article>
    """


def main():
    fila = [i for i in carregar(FILA_PATH) if isinstance(i, dict) and i.get("status") == "pending"]
    historico = carregar(HISTORICO_PATH)
    cards = "\n".join(card(i) for i in fila)
    if not cards:
        cards = '<div class="empty">Nenhuma publicação de grupo está pendente no momento.</div>'

    documento = f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Fila de Grupos — Achados para Casa</title>
<style>
body{{font-family:system-ui,-apple-system,Segoe UI,sans-serif;margin:0;background:#f3f4f6;color:#111827}}
main{{max-width:1100px;margin:0 auto;padding:28px 18px 60px}}
header{{margin-bottom:24px}} h1{{margin:0 0 8px}} .lead{{color:#4b5563}}
.summary{{display:flex;gap:12px;flex-wrap:wrap;margin:18px 0 26px}} .pill{{background:#fff;border:1px solid #e5e7eb;border-radius:999px;padding:8px 12px}}
.card{{background:#fff;border:1px solid #e5e7eb;border-radius:16px;padding:20px;margin:0 0 18px;box-shadow:0 3px 12px rgba(0,0,0,.05)}}
.status{{font-size:12px;font-weight:800;color:#92400e;background:#fef3c7;display:inline-block;padding:5px 8px;border-radius:999px}}
.meta{{color:#6b7280;font-size:13px}} textarea{{width:100%;min-height:180px;box-sizing:border-box;padding:14px;border:1px solid #d1d5db;border-radius:10px;resize:vertical;font:inherit;line-height:1.5}}
.actions{{display:flex;gap:8px;flex-wrap:wrap;margin-top:14px}} .btn{{appearance:none;border:1px solid #d1d5db;background:#fff;color:#111827;text-decoration:none;padding:10px 12px;border-radius:9px;cursor:pointer;font:inherit}}
.btn:hover{{background:#f9fafb}} .primary{{background:#1877f2;color:white;border-color:#1877f2}} .primary:hover{{background:#166fe5}}
.empty{{background:#fff;border:1px dashed #d1d5db;border-radius:14px;padding:28px;color:#6b7280;text-align:center}}
.toast{{position:fixed;right:18px;bottom:18px;background:#111827;color:#fff;padding:10px 14px;border-radius:10px;opacity:0;transition:.2s;pointer-events:none}}
</style>
</head>
<body>
<main>
<header><h1>Fila assistida de grupos do Facebook</h1><div class="lead">O sistema prepara texto, artigo, imagem e grupo. A publicação final continua manual dentro do Facebook.</div></header>
<div class="summary"><div class="pill">Pendentes: {len(fila)}</div><div class="pill">Histórico: {len(historico)}</div><div class="pill">Publicação automática em grupos: desativada</div></div>
{cards}
</main>
<div id="toast" class="toast">Copiado</div>
<script>
function toast(msg){{const t=document.getElementById('toast');t.textContent=msg;t.style.opacity='1';setTimeout(()=>t.style.opacity='0',1600)}}
async function copyValue(v){{try{{await navigator.clipboard.writeText(v);toast('Copiado para a área de transferência')}}catch(e){{prompt('Copie manualmente:',v)}}}}
function copyData(btn){{copyValue(btn.dataset.copy||'')}}
async function markPublished(btn){{await copyValue(btn.dataset.copy||'');window.open('{ACTIONS_URL}','_blank','noopener');toast('Queue ID copiado. Cole no workflow de registro.')}}
</script>
</body>
</html>
"""
    SAIDA_PATH.parent.mkdir(parents=True, exist_ok=True)
    SAIDA_PATH.write_text(documento, encoding="utf-8")
    print("Painel gerado:", SAIDA_PATH)
    print("Pendentes:", len(fila), "| Histórico:", len(historico))


if __name__ == "__main__":
    main()
