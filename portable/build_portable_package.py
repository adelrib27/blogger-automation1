#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import shutil
import stat
import sys
import textwrap
import zipfile
from datetime import datetime, timezone
from pathlib import Path

PACKAGE_NAME = "Blogger_Automation_Unificado_2026-11-02_FINAL"
SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", ".mypy_cache", "node_modules", "backups", "logs"}
SKIP_SUFFIXES = {".pyc", ".pyo", ".zip", ".mp4", ".mov", ".avi"}
SECRET_NAME_RE = re.compile(r"(^|[._-])(client[_-]?secret|credentials|token|secrets?)([._-]|$)", re.I)
ALLOW_SECRET_NAMES = {".env.example", "plugin.json", ".app.json", "plugin-metadata.json", "worker-metadata.json"}


def should_skip(path: Path, root: Path) -> bool:
    rel = path.relative_to(root)
    if any(part in SKIP_DIRS for part in rel.parts):
        return True
    if path.is_file() and path.suffix.lower() in SKIP_SUFFIXES:
        return True
    name = path.name
    if path.is_file() and SECRET_NAME_RE.search(name) and name not in ALLOW_SECRET_NAMES:
        return True
    return False


def copy_tree_filtered(src: Path, dst: Path) -> None:
    if not src.exists():
        return
    for path in src.rglob("*"):
        if should_skip(path, src):
            continue
        rel = path.relative_to(src)
        target = dst / rel
        if path.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        elif path.is_file():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.replace("\r\n", "\n").rstrip() + "\n", encoding="utf-8")


def unified_requirements() -> str:
    return """\
google-api-python-client
google-auth
google-auth-httplib2
google-auth-oauthlib
google-genai
requests
cloudinary
Pillow
playwright>=1.55,<2
"""


def env_example() -> str:
    return """\
# =============================================================
# Blogger Automation — copie para .env e preencha localmente.
# NUNCA envie .env, credentials.json ou tokens para Git/GitHub.
# =============================================================

# OAuth 2.0 Blogger API v3 (gerado por: python run.py oauth ...)
BLOGGER_CLIENT_ID=
BLOGGER_CLIENT_SECRET=
BLOGGER_REFRESH_TOKEN=

# Alvo Blogger. Preencha depois de criar/selecionar o blog.
BLOGGER_BLOG_ID=
BLOGGER_STORE_PAGE_ID=
BLOGGER_STORE_POST_ID=
BLOGGER_STORE_PAGE_URL=

# Shopee Affiliate/Open API
SHOPEE_APP_ID=18352820579
SHOPEE_SECRET=
SHOPEE_TOP_N=180

# Opcional: geração de conteúdo/imagem se os seus fluxos usarem Google GenAI.
GOOGLE_API_KEY=

# Runner local Blogger (Chrome/CDP)
# Gere um valor aleatório com 32+ caracteres; não reutilize senha pessoal.
BLOGGER_RUNNER_TOKEN=
BLOGGER_RUNNER_PORT=8765
BLOGGER_CDP_URL=http://127.0.0.1:9222
BLOGGER_DIAGNOSTICS_DIR=logs/browser_diagnostics

# Fuso canônico do projeto
BLOGGER_TIMEZONE=America/Recife
"""


def gitignore() -> str:
    return """\
.env
.env.*
!.env.example
secrets/*
!secrets/.gitkeep
*.token.json
credentials*.json
client_secret*.json
__pycache__/
*.py[cod]
.venv/
venv/
logs/
backups/
"""


def oauth_script() -> str:
    return r'''#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPE = "https://www.googleapis.com/auth/blogger"


def main() -> int:
    p = argparse.ArgumentParser(description="Autoriza Blogger API v3 via OAuth Desktop e grava credenciais locais.")
    p.add_argument("--credentials", required=True, help="JSON do cliente OAuth Desktop baixado do Google Cloud.")
    p.add_argument("--output", default="secrets/blogger_oauth.json")
    p.add_argument("--env-output", default=".env.oauth")
    args = p.parse_args()

    credentials_path = Path(args.credentials).resolve()
    if not credentials_path.exists():
        raise SystemExit(f"Arquivo OAuth não encontrado: {credentials_path}")

    flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), scopes=[SCOPE])
    creds = flow.run_local_server(
        host="127.0.0.1",
        port=0,
        open_browser=True,
        access_type="offline",
        prompt="consent",
        authorization_prompt_message="Abra esta URL no navegador para autorizar o Blogger: {url}",
        success_message="Autorização concluída. Você pode fechar esta aba e voltar ao terminal.",
    )
    if not creds.refresh_token:
        raise SystemExit(
            "O Google não devolveu refresh_token. Revogue o acesso anterior do app ou rode novamente com consentimento."
        )

    cfg = json.loads(credentials_path.read_text(encoding="utf-8"))
    client = cfg.get("installed") or cfg.get("web") or {}
    client_id = str(client.get("client_id") or "")
    client_secret = str(client.get("client_secret") or "")
    if not client_id:
        raise SystemExit("client_id ausente no JSON OAuth.")

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "scopes": list(creds.scopes or [SCOPE]),
    }
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    env_out = Path(args.env_output)
    env_out.write_text(
        "BLOGGER_CLIENT_ID=" + client_id + "\n"
        + "BLOGGER_CLIENT_SECRET=" + client_secret + "\n"
        + "BLOGGER_REFRESH_TOKEN=" + creds.refresh_token + "\n",
        encoding="utf-8",
    )
    print(f"OK: OAuth Blogger autorizado. Credenciais locais: {out}")
    print(f"OK: variáveis para copiar ao .env: {env_out}")
    print("ATENÇÃO: esses dois arquivos são secretos e estão cobertos pelo .gitignore.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def api_smoke_script() -> str:
    return r'''#!/usr/bin/env python3
from __future__ import annotations

import json
import os

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPE = "https://www.googleapis.com/auth/blogger"


def required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Variável ausente: {name}")
    return value


def service():
    creds = Credentials(
        token=None,
        refresh_token=required("BLOGGER_REFRESH_TOKEN"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=required("BLOGGER_CLIENT_ID"),
        client_secret=required("BLOGGER_CLIENT_SECRET"),
        scopes=[SCOPE],
    )
    return build("blogger", "v3", credentials=creds, cache_discovery=False)


def main() -> int:
    response = service().blogs().listByUser(userId="self").execute()
    items = [
        {"id": str(x.get("id") or ""), "name": x.get("name"), "url": x.get("url")}
        for x in (response.get("items") or [])
    ]
    print(json.dumps({"ok": True, "blogs": items}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def publish_pages_script() -> str:
    return r'''#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPE = "https://www.googleapis.com/auth/blogger"


def req(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Variável ausente: {name}")
    return value


def blogger():
    creds = Credentials(
        token=None,
        refresh_token=req("BLOGGER_REFRESH_TOKEN"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=req("BLOGGER_CLIENT_ID"),
        client_secret=req("BLOGGER_CLIENT_SECRET"),
        scopes=[SCOPE],
    )
    return build("blogger", "v3", credentials=creds, cache_discovery=False)


def list_pages(service, blog_id: str) -> list[dict]:
    result = []
    token = None
    while True:
        kwargs = {"blogId": blog_id, "status": "LIVE", "fetchBodies": True, "maxResults": 100}
        if token:
            kwargs["pageToken"] = token
        response = service.pages().list(**kwargs).execute()
        result.extend(response.get("items") or [])
        token = response.get("nextPageToken")
        if not token:
            return result


def main() -> int:
    p = argparse.ArgumentParser(description="Publica/atualiza as 6 páginas V20 a partir do checkpoint do provisionamento.")
    p.add_argument("--checkpoint", required=True)
    p.add_argument("--confirm", required=True)
    args = p.parse_args()
    if args.confirm != "PUBLISH V20 PAGES":
        raise SystemExit('Confirmação inválida. Use exatamente: PUBLISH V20 PAGES')

    data = json.loads(Path(args.checkpoint).read_text(encoding="utf-8"))
    blog_id = str(data.get("blog_id") or "")
    pages = data.get("pages_to_publish") or []
    if not blog_id.isdigit() or len(pages) != 6:
        raise SystemExit("Checkpoint inválido: esperado blog_id numérico e 6 páginas.")

    service = blogger()
    existing = {str(x.get("title") or "").strip().casefold(): x for x in list_pages(service, blog_id)}
    done = []
    for spec in pages:
        title = str(spec.get("title") or "").strip()
        content = str(spec.get("content") or "")
        if not title or not content:
            raise SystemExit(f"Página inválida no manifesto: {spec.get('key')!r}")
        current = existing.get(title.casefold())
        if current:
            item = service.pages().update(
                blogId=blog_id,
                pageId=str(current["id"]),
                body={"title": title, "content": content},
            ).execute()
            action = "updated"
        else:
            item = service.pages().insert(
                blogId=blog_id,
                isDraft=False,
                body={"title": title, "content": content},
            ).execute()
            action = "created"
        done.append({"key": spec.get("key"), "id": str(item.get("id") or ""), "url": item.get("url"), "action": action})

    verify = list_pages(service, blog_id)
    titles = {str(x.get("title") or "").strip().casefold() for x in verify}
    missing = [str(p.get("title") or "") for p in pages if str(p.get("title") or "").strip().casefold() not in titles]
    if missing:
        raise SystemExit("Validação falhou; páginas ausentes: " + repr(missing))
    print(json.dumps({"status": "BLOGGER_V20_PAGES_PUBLISHED", "blog_id": blog_id, "pages": done}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def unified_run_script() -> str:
    return r'''#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import secrets
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def load_env(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def run(cmd: list[str], cwd: Path | None = None) -> int:
    print(">>> " + " ".join(str(x) for x in cmd), flush=True)
    return subprocess.call(cmd, cwd=str(cwd or ROOT), env=os.environ.copy())


def doctor() -> int:
    print("Blogger Automation — diagnóstico")
    print("Python:", sys.version.replace("\n", " "))
    checks = {
        "src": ROOT / "src",
        "blogger_stores": ROOT / "blogger_stores" / "src",
        "local_runner": ROOT / "local_runner" / "local_service_v08.py",
        "tema_v20": ROOT / "themes" / "blogger_modelo_v20",
    }
    ok = True
    for name, path in checks.items():
        present = path.exists()
        ok = ok and present
        print(f"{name}: {'OK' if present else 'AUSENTE'} — {path}")

    for name in ("BLOGGER_CLIENT_ID", "BLOGGER_CLIENT_SECRET", "BLOGGER_REFRESH_TOKEN", "SHOPEE_APP_ID", "SHOPEE_SECRET"):
        present = bool(os.getenv(name, "").strip())
        print(f"env {name}: {'OK' if present else 'NÃO CONFIGURADA'}")

    cdp = os.getenv("BLOGGER_CDP_URL", "http://127.0.0.1:9222").rstrip("/") + "/json/version"
    try:
        with urllib.request.urlopen(cdp, timeout=2) as r:
            print("Chrome CDP: OK HTTP", r.status)
    except Exception as exc:
        print("Chrome CDP: indisponível —", str(exc)[:180])

    token = os.getenv("BLOGGER_RUNNER_TOKEN", "")
    if token:
        port = os.getenv("BLOGGER_RUNNER_PORT", "8765")
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/v1/health",
            headers={"Authorization": f"Bearer {token}"},
        )
        try:
            with urllib.request.urlopen(req, timeout=2) as r:
                print("Runner local: OK HTTP", r.status)
        except Exception as exc:
            print("Runner local: indisponível —", str(exc)[:180])
    else:
        print("Runner local: token não configurado")
    return 0 if ok else 2


def main() -> int:
    load_env(ROOT / ".env")
    p = argparse.ArgumentParser(description="Entrada unificada do Blogger Automation portátil.")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("doctor")
    o = sub.add_parser("oauth")
    o.add_argument("--credentials", required=True)
    o.add_argument("--output", default="secrets/blogger_oauth.json")
    a = sub.add_parser("api-smoke")
    sub.add_parser("policy-test")
    sub.add_parser("runner")
    g = sub.add_parser("generate-runner-token")
    g.add_argument("--length", type=int, default=48)
    pr = sub.add_parser("provision-blog")
    pr.add_argument("--title", required=True)
    pr.add_argument("--address", required=True)
    pr.add_argument("--description", required=True)
    pr.add_argument("--search-description", required=True)
    pr.add_argument("--timezone", default="America/Recife")
    pr.add_argument("--palette", default="auto")
    pg = sub.add_parser("publish-pages")
    pg.add_argument("--checkpoint", required=True)
    s = sub.add_parser("script")
    s.add_argument("path")
    s.add_argument("args", nargs=argparse.REMAINDER)
    args = p.parse_args()

    py = sys.executable
    if args.cmd == "doctor":
        return doctor()
    if args.cmd == "oauth":
        return run([py, str(ROOT / "scripts" / "oauth_blogger_setup.py"), "--credentials", args.credentials, "--output", args.output])
    if args.cmd == "api-smoke":
        return run([py, str(ROOT / "scripts" / "blogger_api_smoke.py")])
    if args.cmd == "policy-test":
        env = os.environ.copy()
        env["PYTHONPATH"] = str(ROOT / "src")
        return subprocess.call([py, str(ROOT / "src" / "blogger_policy_guard_self_test.py")], cwd=str(ROOT), env=env)
    if args.cmd == "runner":
        return run([py, "local_service_v08.py"], cwd=ROOT / "local_runner")
    if args.cmd == "generate-runner-token":
        print(secrets.token_urlsafe(max(32, args.length)))
        return 0
    if args.cmd == "provision-blog":
        return run([
            py, "provision_new_blog_v20.py",
            "--title", args.title,
            "--address", args.address,
            "--description", args.description,
            "--search-description", args.search_description,
            "--timezone", args.timezone,
            "--palette", args.palette,
            "--confirm", "PROVISION BLOG V20",
        ], cwd=ROOT / "local_runner")
    if args.cmd == "publish-pages":
        return run([py, str(ROOT / "scripts" / "publish_v20_pages.py"), "--checkpoint", args.checkpoint, "--confirm", "PUBLISH V20 PAGES"])
    if args.cmd == "script":
        target = (ROOT / args.path).resolve()
        if ROOT not in target.parents:
            raise SystemExit("Caminho fora do pacote bloqueado.")
        return run([py, str(target), *args.args])
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
'''


def leia_me() -> str:
    return """\
BLOGGER AUTOMATION — PACOTE PORTÁTIL UNIFICADO
===============================================
Snapshot final: 02/11/2026

OBJETIVO
--------
Este pacote reúne o sistema Python deste projeto para ser reinstalado em outro PC e usado com outra conta Google/ChatGPT sem depender do filesystem da máquina original.

Inclui:
- Blogger API v3: posts, páginas, leitura, publicação, reversão e auditoria;
- OAuth 2.0 Desktop para gerar novas credenciais localmente;
- geração/editorial/SEO e Policy Guard;
- Shopee: seleção, filtros semânticos, links e lojas 20+12;
- automações de lojas da rede e Casa Prática Lab;
- Tema MODELO V20 e assets/configurações;
- Local Runner v0.8 via Chrome oficial + Playwright/CDP para criar blog, configurar settings e aplicar tema;
- infraestrutura de referência Cloudflare/ChatGPT sem secrets;
- GitHub Actions permanentes como referência;
- scripts de diagnóstico e entrada unificada run.py.

COMECE POR
----------
1. Leia instrucoes.txt por inteiro.
2. Execute instalar_windows.bat (Windows) ou crie um venv e instale requirements.txt.
3. Copie .env.example para .env e NÃO publique esse arquivo.
4. Configure OAuth com: python run.py oauth --credentials secrets\\client_secret_desktop.json
5. Rode: python run.py doctor

SEGURANÇA
---------
Nenhum client secret, refresh token, Shopee Secret, token do runner ou perfil do Chrome da máquina original é incluído.
O diretório secrets/ nasce vazio.

IMPORTANTE SOBRE CHATGPT
------------------------
O sistema Python funciona sem ChatGPT Work. Para controlá-lo a partir de outra conta do ChatGPT, a conexão/plugin privado e o gateway Cloudflare precisam ser criados/conectados nessa outra conta; identidades de plugin e tokens da conta antiga não são transferíveis pelo ZIP.

ARQUIVOS-CHAVE
--------------
- run.py: entrada unificada
- instrucoes.txt: instalação do zero
- requirements.txt: dependências Python
- .env.example: variáveis necessárias
- scripts/oauth_blogger_setup.py: OAuth local
- scripts/blogger_api_smoke.py: teste da Blogger API
- local_runner/: criação/configuração/tema via Chrome
- src/: automação principal
- blogger_stores/: lojas
- config/: perfis Shopee/semântica
- themes/ e blogger_themes/: temas
- infrastructure/: Cloudflare/ChatGPT backups sem secrets
- MANIFEST.json e SHA256SUMS.txt: integridade do pacote
"""


def instructions() -> str:
    return """\
INSTRUÇÕES — BLOGGER AUTOMATION UNIFICADO
========================================
Versão portátil final: 02/11/2026
Fuso canônico do projeto: America/Recife

0) PRINCÍPIO DO SISTEMA
-----------------------
Há duas camadas complementares:

A. Blogger API v3 (OAuth 2.0)
   Posts, páginas, leitura/escrita, publicação e auditorias.

B. Local Runner + Chrome oficial + Playwright/CDP
   Criação de blog novo, configurações administrativas e aplicação/backup do tema V20.

Isso é intencional. A Blogger API v3 não oferece método para criar um blog novo, por isso a criação usa a interface oficial do Blogger controlada pelo Chrome.

1) PRÉ-REQUISITOS NO NOVO PC
----------------------------
Recomendado:
- Windows 10/11 64-bit;
- Python 3.12.x;
- Google Chrome oficial atualizado;
- acesso à conta Google que será dona dos blogs;
- credenciais da sua API Shopee (AppID e Secret);
- opcional: Git e conta GitHub se quiser GitHub Actions.

Confira Python:
  py -3.12 --version

2) INSTALAR O PACOTE
--------------------
Extraia o ZIP para uma pasta simples, por exemplo:
  C:\Blogger-Automation-Unificado

No Prompt/PowerShell:
  cd C:\Blogger-Automation-Unificado
  py -3.12 -m venv .venv
  .venv\Scripts\python.exe -m pip install --upgrade pip
  .venv\Scripts\python.exe -m pip install -r requirements.txt

Ou execute:
  instalar_windows.bat

Depois:
  copy .env.example .env

3) GOOGLE CLOUD — ATIVAR BLOGGER API v3
----------------------------------------
Na nova conta/projeto do Google Cloud:

3.1 Crie ou selecione um projeto no Google Cloud Console.
3.2 Abra a Biblioteca de APIs e procure "Blogger API v3".
3.3 Habilite a API no projeto.

Documentação oficial de referência:
  https://developers.google.com/blogger/docs/3.0/getting_started

4) GOOGLE AUTH PLATFORM / OAUTH 2.0
-----------------------------------
Use OAuth de APLICATIVO PARA COMPUTADOR (Desktop app). Não use Service Account para controlar a conta Blogger do usuário.

4.1 Abra Google Cloud Console > Google Auth Platform.
4.2 Se for a primeira vez, configure o aplicativo/consentimento (nome do app e email de suporte).
4.3 Em Audience/Público, configure de acordo com sua conta. Se o aplicativo estiver em modo de teste, adicione a conta Google que vai autorizar como usuário de teste.
4.4 Em Data Access/Escopos, o sistema precisa do escopo:
    https://www.googleapis.com/auth/blogger
    Esse escopo permite gerenciar a conta Blogger autorizada.
4.5 Vá para Google Auth Platform > Clients.
4.6 Clique em Create Client / Criar cliente.
4.7 Application type / Tipo: Desktop app / App para computador.
4.8 Dê um nome, por exemplo: Blogger Automation PC Novo.
4.9 Crie o cliente e baixe o JSON.
4.10 Salve o arquivo SOMENTE neste PC como:
     secrets\client_secret_desktop.json

Referências oficiais atuais:
  https://developers.google.com/identity/protocols/oauth2/native-app
  https://developers.google.com/identity/protocols/oauth2/

5) GERAR REFRESH TOKEN NA NOVA MÁQUINA
--------------------------------------
Com o ambiente virtual instalado:

  .venv\Scripts\python.exe run.py oauth --credentials secrets\client_secret_desktop.json

O navegador abrirá. Entre com a conta Google dona dos blogs e autorize o escopo Blogger.
O script cria localmente:
  secrets\blogger_oauth.json
  .env.oauth

Copie as 3 linhas de .env.oauth para o seu .env:
  BLOGGER_CLIENT_ID=...
  BLOGGER_CLIENT_SECRET=...
  BLOGGER_REFRESH_TOKEN=...

Não envie esses valores para o GitHub ou para outra pessoa.

Teste:
  .venv\Scripts\python.exe run.py api-smoke

O comando deve listar os blogs acessíveis pela conta autorizada.

6) CONFIGURAR SHOPEE
--------------------
Edite .env:
  SHOPEE_APP_ID=18352820579
  SHOPEE_SECRET=SEU_SECRET_REAL

O AppID acima é o AppID deste projeto. O Secret nunca é incluído no pacote.
Se você estiver usando outra aplicação Shopee, substitua ambos pelos valores dela.

7) TESTAR O POLICY GUARD
------------------------
  .venv\Scripts\python.exe run.py policy-test

Somente continue para escrita se o teste terminar em PASS.

8) PREPARAR O CHROME PARA O LOCAL RUNNER
----------------------------------------
Feche instâncias de teste anteriores e execute iniciar_chrome_blogger.bat.
Ele abre um perfil separado em:
  C:\Blogger-Automator\chrome-debug-profile

e expõe CDP APENAS em loopback:
  http://127.0.0.1:9222

No Chrome que abrir:
- entre manualmente na conta Google correta;
- abra https://www.blogger.com/;
- confirme visualmente que a conta possui o acesso esperado.

Nunca exponha a porta 9222 na rede/internet.

9) CONFIGURAR TOKEN DO RUNNER
-----------------------------
Gere um token aleatório:
  .venv\Scripts\python.exe run.py generate-runner-token

Copie o resultado para .env:
  BLOGGER_RUNNER_TOKEN=<valor gerado>

O token precisa ter 32+ caracteres.

10) INICIAR O RUNNER LOCAL v0.8
-------------------------------
Em outro terminal:
  .venv\Scripts\python.exe run.py runner

Ele escuta apenas:
  127.0.0.1:8765

Diagnóstico:
  .venv\Scripts\python.exe run.py doctor

O doctor deve mostrar Chrome CDP e Runner local como OK quando ambos estiverem em execução.

11) CRIAR UM BLOG NOVO DO ZERO
-------------------------------
A criação é destrutiva/externa e exige confirmação interna explícita. Exemplo:

  .venv\Scripts\python.exe run.py provision-blog ^
    --title "Meu Blog" ^
    --address "meu-blog-endereco" ^
    --description "Descrição do blog" ^
    --search-description "Descrição curta para mecanismos de busca" ^
    --timezone "America/Recife" ^
    --palette auto

O fluxo faz, com guardas fail-closed:
- criação do blog pelo Blogger Admin;
- validação do Blog ID;
- descrição e search description;
- fuso horário;
- backup/normalização do tema anterior;
- renderização/aplicação do MODELO V20;
- validação pública;
- geração de checkpoint com manifesto das 6 páginas.

O checkpoint aparece em:
  logs\provisioning\provision-v20-*.json

12) PUBLICAR AS 6 PÁGINAS V20 VIA API
-------------------------------------
Depois do provisionamento:

  .venv\Scripts\python.exe run.py publish-pages --checkpoint "CAMINHO_DO_CHECKPOINT.json"

O comando cria/atualiza:
- Sobre
- Afiliados
- Contato
- Privacidade
- Termos
- LOJA

e valida que as seis existem publicamente na API.

13) AUTOMAÇÃO DA LOJA
---------------------
Os motores existentes estão em:
  blogger_stores\src\
  radar_tech_br\src\
  config\

O sistema atual trabalha com:
- SAFE Shopee primeiro;
- filtros semânticos por nicho;
- 20 produtos / 5 categorias;
- hero 12 cards onde aplicável;
- Policy Guard antes de live;
- persistência somente depois da aceitação pública;
- rotação para evitar vitrine parada.

Para um blog novo com nicho novo NÃO copie cegamente regras de outro nicho.
Crie/ajuste um arquivo de config e intent_rules em config/, execute SAFE + validate + dry-run e só então habilite o LIVE.
Use os módulos Casa Prática Lab como referência do contrato mais novo:
  blogger_stores\src\casa_pratica_lab_store.py
  blogger_stores\src\casa_pratica_lab_store_page.py
  blogger_stores\src\blogger_new_blog_store_page_target.py
  blogger_stores\src\blogger_store_share_card.py
  blogger_stores\src\casa_pratica_lab_public_acceptance.py

14) EXECUTAR QUALQUER MÓDULO PELO ENTRYPOINT ÚNICO
-------------------------------------------------
Exemplo:
  .venv\Scripts\python.exe run.py script blogger_stores\src\casa_pratica_lab_public_acceptance.py

Para scripts que dependem de PYTHONPATH específico, prefira os workflows de referência ou rode com os diretórios documentados no próprio módulo.

15) GITHUB ACTIONS (OPCIONAL)
-----------------------------
As automações permanentes estão em:
  .github\workflows\

Em um repositório novo, crie os GitHub Actions Secrets necessários, por exemplo:
  BLOGGER_CLIENT_ID
  BLOGGER_CLIENT_SECRET
  BLOGGER_REFRESH_TOKEN
  SHOPEE_APP_ID
  SHOPEE_SECRET

Não copie secrets da conta antiga por arquivo.

16) USAR EM OUTRA CONTA DO CHATGPT — SEM WORK
---------------------------------------------
O Python NÃO depende do ChatGPT Work.

Para controlar o runner a partir de outra conta do ChatGPT, você precisa criar/conectar nessa nova conta um plugin/app privado equivalente. O pacote inclui como referência:
  infrastructure\chatgpt\blogger-local-runner\
  infrastructure\cloudflare\blogger-local-runner-gateway\

A topologia é:
  ChatGPT -> plugin/MCP privado -> Cloudflare Worker -> serviço/VPC -> runner 127.0.0.1:8765 -> Chrome -> Blogger

Os IDs antigos de plugin, OAuth tokens e secrets NÃO são portáveis entre contas. Na nova conta:
- implante/configure seu próprio gateway;
- defina um OAUTH_SECRET novo no Cloudflare;
- conecte o serviço que alcança o runner local de forma privada;
- crie/conecte o plugin privado na nova conta apontando para o endpoint MCP do seu gateway;
- faça a autorização da conexão explicitamente na nova conta.

Nunca exponha diretamente 127.0.0.1:8765 ou 9222 na internet.

17) BACKUP E APLICAÇÃO DE TEMA
------------------------------
O runner portátil inclui:
- backup_theme_auto.py (autocontido + validação estrutural);
- apply_theme_safe.py (versionado no fechamento de portabilidade);
- apply_theme_auto.py;
- run_with_cdp_resilience_v08.py;
- install_modelo_v20_adoption.py;
- runtime_update_guard_v08.py.

A aplicação exige:
- Blog ID exato;
- arquivo literal theme.xml;
- backup validado antes da aplicação;
- confirmação explícita;
- validação do marcador no blog público.

18) CASA PRÁTICA LAB — CONTRATO FINAL USADO COMO REFERÊNCIA
----------------------------------------------------------
O fechamento de 02/11/2026 validou:
- Page LOJA pública 20+12;
- layout amplo;
- carousel com um slide ativo, setas/dots e rotação;
- share card branco com ícone verde e compartilhamento funcional;
- Store Post técnico fora da home;
- 3/3 artigos editoriais presentes e com imagem;
- Policy Guard;
- retry de HTTP 429;
- writer permanente preservando o share card.

19) CHECKLIST ANTES DE QUALQUER LIVE
------------------------------------
[ ] python run.py doctor
[ ] python run.py api-smoke
[ ] python run.py policy-test
[ ] conta Google correta no Chrome dedicado
[ ] Blog ID confirmado
[ ] backup do tema validado
[ ] SAFE Shopee PASS
[ ] semântica PASS
[ ] dry-run PASS
[ ] Policy Guard PASS
[ ] só então live
[ ] validação pública depois da escrita

20) O QUE NÃO ESTÁ DENTRO DO ZIP
--------------------------------
Por segurança:
- refresh tokens reais;
- client secrets reais;
- Shopee Secret;
- BLOGGER_RUNNER_TOKEN;
- OAUTH_SECRET do Cloudflare;
- perfil/login do Chrome;
- cookies/sessões;
- arquivos de credenciais da máquina original.

Eles precisam ser recriados/configurados na nova máquina/conta.
"""


def windows_install_bat() -> str:
    return r'''@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
  echo Python Launcher ^(py^) nao encontrado. Instale Python 3.12 e tente novamente.
  exit /b 1
)
py -3.12 -m venv .venv
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe -m pip install --upgrade pip
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 exit /b 1
if not exist .env copy /Y .env.example .env >nul
if not exist secrets mkdir secrets
echo.
echo INSTALACAO CONCLUIDA.
echo Edite .env, configure OAuth conforme instrucoes.txt e rode:
echo   .venv\Scripts\python.exe run.py doctor
endlocal
'''


def start_chrome_bat() -> str:
    return r'''@echo off
setlocal
set "CHROME=%ProgramFiles%\Google\Chrome\Application\chrome.exe"
if not exist "%CHROME%" set "CHROME=%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"
if not exist "%CHROME%" (
  echo Google Chrome oficial nao encontrado.
  exit /b 1
)
if not exist "C:\Blogger-Automator" mkdir "C:\Blogger-Automator"
start "Blogger Chrome CDP" "%CHROME%" --remote-debugging-port=9222 --remote-debugging-address=127.0.0.1 --user-data-dir="C:\Blogger-Automator\chrome-debug-profile" "https://www.blogger.com/"
echo Chrome Blogger iniciado em perfil separado, CDP loopback 127.0.0.1:9222.
endlocal
'''


def scan_imports(root: Path) -> dict:
    counts: dict[str, int] = {}
    for path in root.rglob("*.py"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [x.name.split(".")[0] for x in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module.split(".")[0]]
            for name in names:
                counts[name] = counts.get(name, 0) + 1
    return dict(sorted(counts.items()))


def secret_scan(root: Path) -> list[str]:
    findings = []
    patterns = [
        re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
        re.compile(r"\b1//[A-Za-z0-9._-]{20,}"),
        re.compile(r"\bya29\.[A-Za-z0-9._-]{20,}"),
        re.compile(r"\bGOCSPX-[A-Za-z0-9_-]{15,}"),
    ]
    for path in root.rglob("*"):
        if not path.is_file() or path.stat().st_size > 3_000_000:
            continue
        if path.name in {"MANIFEST.json", "SHA256SUMS.txt"}:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for pattern in patterns:
            if pattern.search(text):
                findings.append(str(path.relative_to(root)))
                break
    return findings


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_manifest(stage: Path, metadata: dict) -> None:
    file_entries = []
    for path in sorted(stage.rglob("*")):
        if not path.is_file() or path.name in {"MANIFEST.json", "SHA256SUMS.txt"}:
            continue
        file_entries.append({
            "path": path.relative_to(stage).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        })
    metadata["files"] = file_entries
    metadata["file_count"] = len(file_entries)
    write_text(stage / "MANIFEST.json", json.dumps(metadata, ensure_ascii=False, indent=2))
    sums = []
    for path in sorted(stage.rglob("*")):
        if path.is_file() and path.name != "SHA256SUMS.txt":
            sums.append(f"{sha256_file(path)}  {path.relative_to(stage).as_posix()}")
    write_text(stage / "SHA256SUMS.txt", "\n".join(sums))


def make_zip(stage: Path, zip_path: Path) -> None:
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in sorted(stage.rglob("*")):
            if path.is_file():
                zf.write(path, arcname=f"{stage.name}/{path.relative_to(stage).as_posix()}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--main-root", required=True)
    parser.add_argument("--runner-root", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    main_root = Path(args.main_root).resolve()
    runner_root = Path(args.runner_root).resolve()
    out = Path(args.output_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    stage = out / PACKAGE_NAME
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True)

    # Copia o snapshot atual inteiro, filtrando somente estado local/segredos/binários transitórios.
    copy_tree_filtered(main_root, stage)
    shutil.rmtree(stage / "portable", ignore_errors=True)

    # Remove workflows one-shot/diagnósticos temporários do pacote operacional.
    wf = stage / ".github" / "workflows"
    if wf.exists():
        for path in wf.glob("*.yml"):
            low = path.name.lower()
            if "_once" in low or "bootstrap" in low or "diag" in low or "snapshot" in low:
                path.unlink(missing_ok=True)

    # Runner validado vive em branch separada: incorpore-o como runtime autocontido.
    runner_src = runner_root / "tools" / "blogger_safe_automator_v0_2"
    if not runner_src.exists():
        raise SystemExit(f"Runner não encontrado: {runner_src}")
    copy_tree_filtered(runner_src, stage / "local_runner")
    # O provisionador usa ROOT/themes; mescle os templates da branch do runner no pacote.
    if (runner_root / "themes").exists():
        copy_tree_filtered(runner_root / "themes", stage / "themes")

    # Entradas portáteis e documentação.
    write_text(stage / "requirements.txt", unified_requirements())
    write_text(stage / ".env.example", env_example())
    write_text(stage / ".gitignore", gitignore())
    write_text(stage / "LEIA-ME-PRIMEIRO.txt", leia_me())
    write_text(stage / "instrucoes.txt", instructions())
    write_text(stage / "run.py", unified_run_script())
    write_text(stage / "scripts" / "oauth_blogger_setup.py", oauth_script())
    write_text(stage / "scripts" / "blogger_api_smoke.py", api_smoke_script())
    write_text(stage / "scripts" / "publish_v20_pages.py", publish_pages_script())
    write_text(stage / "instalar_windows.bat", windows_install_bat())
    write_text(stage / "iniciar_chrome_blogger.bat", start_chrome_bat())
    (stage / "secrets").mkdir(exist_ok=True)
    write_text(stage / "secrets" / ".gitkeep", "")

    # Garanta que o antigo gap de portabilidade realmente foi fechado.
    required = [
        stage / "local_runner" / "local_service_v08.py",
        stage / "local_runner" / "provision_new_blog_v20.py",
        stage / "local_runner" / "backup_theme_auto.py",
        stage / "local_runner" / "apply_theme_safe.py",
        stage / "local_runner" / "apply_theme_auto.py",
        stage / "local_runner" / "run_with_cdp_resilience_v08.py",
        stage / "local_runner" / "install_modelo_v20_adoption.py",
        stage / "themes" / "blogger_modelo_v20" / "pages.json",
        stage / "blogger_stores" / "src" / "blogger_store_share_card.py",
    ]
    missing = [str(p.relative_to(stage)) for p in required if not p.exists()]
    if missing:
        raise SystemExit("Pacote incompleto; arquivos obrigatórios ausentes: " + repr(missing))

    # Compile sintaticamente todo o código empacotado.
    import compileall
    if not compileall.compile_dir(str(stage), quiet=1, force=True):
        raise SystemExit("Falha de sintaxe ao compilar o pacote.")
    for cache in stage.rglob("__pycache__"):
        shutil.rmtree(cache, ignore_errors=True)

    findings = secret_scan(stage)
    if findings:
        raise SystemExit("Possível segredo detectado; build bloqueado: " + repr(findings))

    metadata = {
        "package": PACKAGE_NAME,
        "built_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_repository": "adelrib27/blogger-automation1",
        "main_source": os.getenv("GITHUB_SHA", "unknown"),
        "runner_branch": "blogger-safe-ui-provisioning-v0-2",
        "runner_apply_theme_safe_present": True,
        "credentials_included": False,
        "canonical_timezone": "America/Recife",
        "shopee_app_id_template": "18352820579",
        "components": [
            "Blogger API v3 OAuth",
            "posts/pages/editorial/SEO",
            "Shopee selection + semantic filters",
            "Policy Guard",
            "multi-store automation",
            "Blogger MODELO V20",
            "Local Runner v0.8 + Chrome CDP",
            "new-blog provisioning",
            "store 20+12 + carousel + share card",
            "Cloudflare/ChatGPT integration templates",
        ],
        "python_import_inventory": scan_imports(stage),
    }
    write_manifest(stage, metadata)

    zip_path = out / f"{PACKAGE_NAME}.zip"
    if zip_path.exists():
        zip_path.unlink()
    make_zip(stage, zip_path)
    write_text(out / f"{PACKAGE_NAME}.zip.sha256.txt", f"{sha256_file(zip_path)}  {zip_path.name}")
    print(json.dumps({
        "status": "PORTABLE_PACKAGE_BUILT",
        "stage": str(stage),
        "zip": str(zip_path),
        "zip_sha256": sha256_file(zip_path),
        "files": json.loads((stage / "MANIFEST.json").read_text(encoding="utf-8"))["file_count"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
