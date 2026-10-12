import json
import os
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
FILA_PATH = BASE_DIR / "data" / "facebook_fila_grupos.json"
HISTORICO_PATH = BASE_DIR / "data" / "facebook_grupos_publicados.json"
RESULTADO_PATH = BASE_DIR / "artifacts" / "facebook_grupos_mark_result.json"


def carregar_json(path, padrao):
    if not path.exists():
        return padrao
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return padrao


def salvar_json(path, dados):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def agora_iso():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def main():
    queue_id = str(os.getenv("QUEUE_ID") or "").strip()
    status = str(os.getenv("MARK_STATUS") or "published").strip().lower()
    permalink = str(os.getenv("FACEBOOK_GROUP_POST_URL") or "").strip()
    nota = str(os.getenv("MARK_NOTE") or "").strip()

    if not queue_id:
        raise RuntimeError("QUEUE_ID ausente.")
    if status not in {"published", "skipped"}:
        raise RuntimeError("MARK_STATUS deve ser published ou skipped.")

    fila = carregar_json(FILA_PATH, [])
    historico = carregar_json(HISTORICO_PATH, [])
    if not isinstance(fila, list) or not isinstance(historico, list):
        raise RuntimeError("Fila e histórico precisam ser listas JSON.")

    alvo = None
    nova_fila = []
    for item in fila:
        if isinstance(item, dict) and str(item.get("queue_id") or "") == queue_id:
            if alvo is not None:
                raise RuntimeError("QUEUE_ID duplicado na fila.")
            alvo = item
            continue
        nova_fila.append(item)

    if alvo is None:
        existente = next((i for i in historico if isinstance(i, dict) and str(i.get("queue_id") or "") == queue_id), None)
        if existente:
            salvar_json(RESULTADO_PATH, {"status": "already_recorded", "record": existente})
            print("Item já estava registrado no histórico; nenhuma alteração feita.")
            return
        raise RuntimeError("QUEUE_ID não encontrado na fila.")

    registro = {
        "queue_id": queue_id,
        "post_id": alvo.get("post_id"),
        "group_key": alvo.get("group_key"),
        "status": status,
        "batch_date": alvo.get("batch_date"),
        "created_at": alvo.get("created_at"),
        "recorded_at": agora_iso(),
        "published_at": agora_iso() if status == "published" else None,
        "facebook_post_url": permalink or None,
        "note": nota or None,
        "post": alvo.get("post"),
        "group": alvo.get("group"),
        "copy": alvo.get("copy"),
    }

    historico.append(registro)
    salvar_json(FILA_PATH, nova_fila)
    salvar_json(HISTORICO_PATH, historico)
    salvar_json(RESULTADO_PATH, {"status": "recorded", "record": registro})

    print("QUEUE ID:", queue_id)
    print("Grupo:", (alvo.get("group") or {}).get("nome"))
    print("Status registrado:", status)
    if permalink:
        print("Post URL:", permalink)
    print("FILA DE GRUPOS: registro atualizado.")


if __name__ == "__main__":
    main()
