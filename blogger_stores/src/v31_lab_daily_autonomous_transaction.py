#!/usr/bin/env python3
"""LAB V31: one fail-closed daily transaction (never use for legacy blogs).

Called only by the isolated LAB workflow_dispatch. An existing V23 SAFE_READY
selection is mandatory. No retries of PUT, Git commits or partial transactions
after uncertain network results. Reconcile authenticated state manually.
"""
from __future__ import annotations
import json
import os
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import re
import subprocess
import sys
from urllib import request, error
from zoneinfo import ZoneInfo

SRC = Path(__file__).resolve().parent
CORE = SRC.parent / "v31_core"
for d in (SRC, CORE):
    if str(d) not in sys.path: sys.path.insert(0, str(d))
from v31_daily_candidate_contract_safe import preview_daily_candidate
from v31_rotation_ledger import mark_readback, mark_public_verified, history_commit, validate_state
from v31_etag_sacrificial_live_once import oauth_access_token, list_pages
from v31_public_verify_cloudflare import run as verify_cloudflare

REPO = "adelrib27/blogger-automation1"
BRANCH = "lab/v31r1-shopee-safe-20261103"
BLOG = "4739187376492839837"
PAGE = "2446067640331732447"
PAGE_URL = "https://blog-teste-tema-worpress.blogspot.com/p/loja.html"
PAGE_API = f"https://www.googleapis.com/blogger/v3/blogs/{BLOG}/pages/{PAGE}"
REF = "refs/heads/" + BRANCH
LEDGER = "blogger_stores/v31_lab/state/v31_rotation_ledger.json"
HISTORY = "blogger_stores/v31_lab/state/v31_rotation_history.json"
PROFILE = "blogger_stores/v31_lab/perfil_v31_lab.json"
APPROVAL = "USER_AUTHORIZED_V31_LAB_AUTOMATIC_DAILY_20261104"
LIVE_SET = frozenset({LEDGER, HISTORY})
RECIFE = ZoneInfo("America/Recife")


class Blocked(RuntimeError):
    pass


def need(condition, why):
    if not condition: raise Blocked(why)


def digest(raw: bytes) -> str:
    return sha256(raw).hexdigest()


def strong_etag(tag) -> bool:
    return isinstance(tag, str) and re.fullmatch(r'"[\x21\x23-\x7e]+"', tag) is not None


def canonical(doc: dict) -> bytes:
    return (json.dumps(doc, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def check_environment():
    e = os.environ
    need(e.get("GITHUB_REPOSITORY") == REPO and e.get("GITHUB_REF") == REF,
         "Repositório/branch LAB divergentes")
    need(e.get("GITHUB_EVENT_NAME") == "workflow_dispatch" and e.get("GITHUB_RUN_ATTEMPT") == "1",
         "Somente primeira tentativa do disparo agendado")
    need(e.get("V31_DAILY_ORIGIN") == "MAIN_SCHEDULE_LAB_ONLY" and
         e.get("V31_DAILY_APPROVAL") == APPROVAL,
         "Origem/autorização diária não correspondem")
    need(e.get("GITHUB_WORKFLOW_REF", "").endswith(
         ".github/workflows/v31_lab_daily_autonomous_dispatch.yml@" + REF),
         "Workflow de origem divergente")
    need(re.fullmatch(r"\d+", e.get("GITHUB_RUN_ID", "")) is not None,
         "Identidade da execução ausente")
    need(Path(e.get("GITHUB_WORKSPACE", "/invalid")).resolve() == Path.cwd().resolve(),
         "Checkout inesperado")
    need(e.get("GITHUB_ACTOR") != "dependabot[bot]", "Ator automático proibido")


def git(*args) -> bytes:
    cp = subprocess.run(["git", *args], stdout=subprocess.PIPE,
                        stderr=subprocess.DEVNULL, timeout=60, check=False)
    need(cp.returncode == 0, "Falha do Git: interrompido sem repetição automática")
    return cp.stdout


class GitLease:
    def __init__(self):
        self.head = git("rev-parse", "HEAD").decode().strip()
        self.expect_clean()
        need(self.head == os.getenv("GITHUB_SHA"), "Checkout não corresponde à origem")
        need(self.remote_head() == self.head, "Branch LAB mudou antes da seleção")
    def expect_clean(self):
        need(not git("status", "--porcelain"), "Árvore Git suja; abortado")
    def remote_head(self):
        raw = git("ls-remote", "origin", REF).decode().strip()
        need(re.fullmatch(r"[a-f0-9]{40}\s+" + re.escape(REF), raw) is not None,
             "Remote ref LAB não identificado")
        return raw[:40]
    def read(self, path):
        return git("show", self.head + ":" + path)
    def commit_exact(self, changes: dict[str, bytes], message: str) -> str:
        need(type(changes) is dict and len(changes) in (1, 2),
             "Número de arquivos inesperado")
        backup_names = {k for k in changes if re.fullmatch(
            r"blogger_stores/v31_lab/prewrite_backup/[0-9a-f]{64}/"
            r"LOJA_ANTES_ROTACAO_DIARIA\.html", k)}
        allowed = {frozenset({LEDGER}), frozenset({LEDGER, HISTORY})}
        allowed.update(frozenset({LEDGER, name}) for name in backup_names)
        need(frozenset(changes) in allowed,
             "Caminhos da operação Git fora da allowlist LAB")
        need(self.remote_head() == self.head, "Git mudou antes de commit")
        self.expect_clean()
        for rel, data in changes.items():
            p = Path(rel)
            need(not p.is_symlink() and type(data) is bytes, "Arquivo inválido")
            if rel.startswith("blogger_stores/v31_lab/prewrite_backup/"):
                need(not p.exists(), "Backup já existente: bloquear repetição")
                p.parent.mkdir(parents=True, exist_ok=True)
                with p.open("xb") as f: f.write(data)
            else:
                need(p.is_file(), "Estado canônico inexistente")
                p.write_bytes(data)
        git("add", "--", *sorted(changes))
        staged = git("diff", "--cached", "--name-only").decode().splitlines()
        need(staged == sorted(changes), "Diff Git possui outros caminhos")
        git("-c", "user.name=V31 LAB Daily Guard",
            "-c", "user.email=v31-lab-guard@users.noreply.github.com",
            "commit", "-m", message)
        after = git("rev-parse", "HEAD").decode().strip()
        need(self.remote_head() == self.head, "Branch concorrente mudou após commit")
        # This is deliberately non-force. After a timeout, NEVER retry this push.
        git("push", "origin", "HEAD:" + REF)
        need(self.remote_head() == after, "Não houve confirmação do push remoto")
        for path, raw in changes.items():
            need(git("show", after + ":" + path) == raw,
                 "Readback Git não confere; interrompido")
        changed = git("diff-tree", "--no-commit-id", "--name-only", "-r", after).decode().splitlines()
        need(changed == sorted(changes), "Commit alterou outros arquivos")
        self.head = after
        self.expect_clean()
        return after


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


OPENER = request.build_opener(NoRedirect)


def blogger_call(token: str, method: str, *, payload=None, etag=None):
    need(method in ("GET", "PUT"), "Método Blogger proibido")
    if method == "PUT":
        need(type(payload) is dict and set(payload) == {"kind", "blog", "id", "title", "content"} and
             payload.get("kind") == "blogger#page" and payload.get("id") == PAGE and
             payload.get("blog") == {"id": BLOG} and payload.get("title") == "LOJA",
             "PUT para Blogger fora do contrato")
        need(strong_etag(etag), "PUT condicional exige ETag forte")
    headers = {"Authorization": "Bearer " + token, "Accept": "application/json",
               "User-Agent": "V31-LAB-DAILY-TRANSACTION/1"}
    if method == "PUT":
        headers["If-Match"] = etag
        headers["Content-Type"] = "application/json; charset=utf-8"
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8") if method == "PUT" else None
    req = request.Request(PAGE_API, headers=headers, data=body, method=method)
    try:
        with OPENER.open(req, timeout=35) as resp:
            need(resp.status == 200, "Blogger não confirmou HTTP 200")
            raw = resp.read(250001)
            need(len(raw) < 250001, "Resposta Blogger incompleta/grande")
            return json.loads(raw)
    except error.HTTPError as exc:
        # No body, response headers or token in logs.
        raise Blocked("Blogger HTTP " + str(exc.code) + "; não repetir PUT") from None
    except (error.URLError, TimeoutError, OSError):
        raise Blocked("Resposta Blogger incerta; GET manual antes de qualquer nova ação") from None


def require_live_page(token: str, doc: dict):
    need(type(doc) is dict and str(doc.get("id")) == PAGE and
         str((doc.get("blog") or {}).get("id")) == BLOG and
         doc.get("title") == "LOJA" and doc.get("url") == PAGE_URL,
         "Identidade da Page Blogger divergente")
    need(strong_etag(doc.get("etag")) and
         isinstance(doc.get("content"), str) and
         isinstance(doc.get("updated"), str),
         "Readback da página/ETag ausente")
    # pages.get may omit the status field, so validate against authenticated LIVE inventory.
    inventory = list_pages(token, "live")
    need(sum(str(x.get("id")) == PAGE for x in inventory) == 1,
         "Página não consta no inventário LIVE autenticado")
    return doc["content"].encode("utf-8")


def prepare_before_write(lease: GitLease, token: str, selection_bytes: bytes, *,
                         selection_path: Path, profile_path: Path):
    profile = json.loads(lease.read(PROFILE))
    ledger = json.loads(lease.read(LEDGER))
    history = json.loads(lease.read(HISTORY))
    original_page = blogger_call(token, "GET")
    original = require_live_page(token, original_page)
    sys.path.insert(0, str(Path.cwd() / "src"))
    from blogger_policy_guard import require_product_allowed
    plan = preview_daily_candidate(
        profile=profile, ledger=ledger, history=history,
        selection_bytes=selection_bytes, current_page_bytes=original,
        now=datetime.now(RECIFE), policy_guard=require_product_allowed)
    need(plan["bloggerPutAllowed"] is False and
         plan["gitRemoteWriteAllowed"] is False and
         plan["cronEnabled"] is False, "SAFE retornou permissão inesperada")
    need(plan["selectionSha256"] == digest(selection_bytes) and
         plan["candidateHtmlSha256"] == digest(plan["candidateHtmlBytes"]),
         "Hashes do preflight diferem")
    need(lease.remote_head() == lease.head, "Git mudou durante preflight")
    return profile, ledger, history, original_page, original, plan


def require_public_verification_credentials():
    """Require independent public-proof access BEFORE PLAN or any Blogger PUT."""
    account = os.environ.get("V31_CF_LAB_ACCOUNT_ID", "")
    token = os.environ.get("V31_CF_LAB_BROWSER_TOKEN", "")
    need(re.fullmatch(r"[0-9a-fA-F]{32}", account) is not None,
         "Cloudflare LAB account indisponível: nenhuma reserva permitida")
    need(isinstance(token, str) and len(token.strip()) >= 20,
         "Cloudflare LAB token indisponível: nenhuma reserva permitida")


def exact_backup_verified(lease, path: str, original: bytes) -> bool:
    """Git backup MUST match ALL HTML bytes, including any trailing newline."""
    return type(original) is bytes and lease.read(path) == original


def execute(selection_path: Path, profile_path: Path) -> dict:
    check_environment()
    require_public_verification_credentials()
    need(selection_path.is_file() and profile_path.is_file(),
         "Seleção SAFE e perfil são obrigatórios")
    need(profile_path.resolve() == (Path.cwd()/PROFILE).resolve(),
         "Perfil fora do LAB")
    selection = selection_path.read_bytes()
    need(0 < len(selection) < 1024 * 1024, "Seleção inválida")
    lease = GitLease()
    token = oauth_access_token()
    profile, ledger, history, before_doc, before, plan = prepare_before_write(
        lease, token, selection, selection_path=selection_path,
        profile_path=profile_path)
    oid = plan["operationId"]
    current_sha = plan["currentHtmlSha256"]
    candidate = plan["candidateHtmlBytes"]
    candidate_sha = plan["candidateHtmlSha256"]
    need(oid not in [op["operationId"] for op in ledger["operations"]],
         "Operação pré-existente: não repetir")
    need(lease.remote_head() == lease.head, "Git mudou antes da reserva")

    # Phase 1. PLAN reservation in Git, non-force CAS. No Blogger writes.
    reserve = plan["proposedLedger"]
    reserve_commit = lease.commit_exact({LEDGER: canonical(reserve)},
                                        "V31 LAB auto: reservar PLAN diário, sem Blogger PUT")
    need(json.loads(lease.read(LEDGER))["operations"][-1]["operationId"] == oid,
         "Reserva Git não persistiu")

    # Phase 2. PREWRITE CLAIM and ORIGINAL HTML backup in one atomic Git commit.
    backup_path = (f"blogger_stores/v31_lab/prewrite_backup/{oid}/"
                   "LOJA_ANTES_ROTACAO_DIARIA.html")
    claimed = json.loads(lease.read(LEDGER))
    last = claimed["operations"][-1]
    need(last["status"] == "PLAN" and last["operationId"] == oid and
         "prewriteClaim" not in last, "Claim já realizado")
    last["prewriteClaim"] = {"state": "ATTEMPT_CLAIMED_BEFORE_PUT",
                             "backupSha256": current_sha}
    claim_commit = lease.commit_exact({LEDGER: canonical(claimed),
                                       backup_path: before},
                                      "V31 LAB auto: claim único + backup HTML antes do PUT")
    need(exact_backup_verified(lease, backup_path, before) and
         json.loads(lease.read(LEDGER))["operations"][-1]["prewriteClaim"]["state"] ==
         "ATTEMPT_CLAIMED_BEFORE_PUT", "Backup/claim remoto não confirmado")

    # Phase 3. Verify the original content still exists immediately before PUT.
    live_now = blogger_call(token, "GET")
    current = require_live_page(token, live_now)
    need(digest(current) == current_sha and current == before and
         live_now["etag"] == before_doc["etag"] and
         live_now["updated"] == before_doc["updated"] and
         lease.remote_head() == claim_commit,
         "Estado concorrente após claim: BLOQUEADO antes do PUT")
    need(strong_etag(live_now["etag"]), "ETag forte indisponível")

    # The ONLY Blogger PUT. Never retry in the same run or on rerun.
    put_body = {"kind": "blogger#page", "blog": {"id": BLOG}, "id": PAGE,
                "title": "LOJA", "content": candidate.decode("utf-8")}
    blogger_call(token, "PUT", payload=put_body, etag=live_now["etag"])
    after_doc = blogger_call(token, "GET")
    actual = require_live_page(token, after_doc)
    need(actual == candidate and digest(actual) == candidate_sha and
         after_doc["updated"] != before_doc["updated"],
         "Readback após PUT divergente; não tentar novo PUT")

    # Phase 4. Independent public exact-catalog proof via Cloudflare.
    proof = verify_cloudflare(
        selection_path, profile_path, digest(selection),
        os.environ.get("V31_CF_LAB_ACCOUNT_ID", ""),
        os.environ.get("V31_CF_LAB_BROWSER_TOKEN", ""))
    need(proof["status"] == "PUBLIC_EXACT_PASS" and
         proof["selection_sha256"] == digest(selection) and
         proof["public_http"] == 200 and
         proof["cards"] == proof["images"] == proof["links"] == 16 and
         proof["transport"] == "CLOUDFLARE_BROWSER_RENDERING",
         "Prova pública exata insuficiente; não persistir histórico")
    checked_at = datetime.now(timezone.utc).isoformat()
    # Phase 5. Finalise both Git state documents in ONE non-force CAS commit.
    final = json.loads(lease.read(LEDGER))
    need(final["operations"][-1]["operationId"] == oid and
         final["operations"][-1]["prewriteClaim"]["backupSha256"] == current_sha,
         "Claim remoto divergente na finalização")
    published = mark_readback(final, digest(selection),
                              observed_candidate_sha=candidate_sha)
    op = published["operations"][-1]
    op["pageUpdatedAt"] = after_doc["updated"]
    op["publishRunId"] = int(os.environ["GITHUB_RUN_ID"])
    op["shopeeSelectionRunId"] = int(os.environ["GITHUB_RUN_ID"])
    verified = mark_public_verified(published, digest(selection), proof=proof)
    entries = [{"itemId": str(p["itemId"]), "category": c}
               for c, arr in json.loads(selection)["categories"].items() for p in arr]
    complete, history_new = history_commit(
        verified, digest(selection), history,
        published_items=entries, published_at=after_doc["updated"])
    complete["operations"][-1]["publicProof"] = {
        "transport": proof["transport"], "sourceRun": int(os.environ["GITHUB_RUN_ID"]),
        "verifiedAt": checked_at, "htmlSha256": proof["public_html_sha256"],
        "publicHttp": 200, "cards": 16, "images": 16, "links": 16,
        "categories": 4,
    }
    validate_state(complete)
    need(len(history_new["runs"]) == len(history["runs"]) + 1 and
         len(complete["operations"]) == len(ledger["operations"]) + 1 and
         complete["operations"][-1]["status"] == "PERSISTED",
         "Finalização não adicionou exatamente um ciclo")
    need(lease.remote_head() == claim_commit, "Git mudou após publicação")
    persist = lease.commit_exact(
        {LEDGER: canonical(complete), HISTORY: canonical(history_new)},
        "V31 LAB auto: persistir ledger e histórico após PUBLIC_EXACT_PASS")
    need(json.loads(lease.read(LEDGER))["operations"][-1]["status"] == "PERSISTED" and
         len(json.loads(lease.read(HISTORY))["runs"]) == len(history_new["runs"]),
         "Readback da persistência falhou")
    return {"status": "V31_LAB_DAILY_AUTO_PERSISTED_PUBLIC_EXACT_PASS",
            "operationId": oid, "reserveCommit": reserve_commit,
            "claimCommit": claim_commit, "persistCommit": persist,
            "selectionSha256": digest(selection), "candidateSha256": candidate_sha,
            "putAttempts": 1, "products": 16,
            "publishedAt": after_doc["updated"], "publicVerifiedAt": checked_at,
            "otherBlogsModified": False}


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--selection", type=Path, required=True)
    parser.add_argument("--profile", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = execute(args.selection, args.profile)
        print("V31_LAB_DAILY_RESULT=" + json.dumps(result, sort_keys=True))
        return 0
    except Exception as exc:
        # Do not expose secret values, unexpected HTML or URL response bodies.
        print("V31_LAB_DAILY_STOP=" + json.dumps({
            "errorType": type(exc).__name__, "noAutomaticRetry": True,
            "manualReconciliationRequiredIfClaimed": True,
            "bloggerPutRepeatAllowed": False}, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
