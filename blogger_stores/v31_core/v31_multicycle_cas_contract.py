"""V31 LAB: pure *offline* compare-and-swap reservation contract.

No Git, Blogger, Shopee, Cloudflare or filesystem side effects. The caller must
independently authenticate the remote Git refs/blobs, perform any one-file
reservation commit via non-force push, re-read the remote head, and apply a
separate explicitly authorised Blogger write gate. Nothing here grants PUT,
Git writes, publication, cron or promotion to new blogs.
"""
from __future__ import annotations
from hashlib import sha1, sha256
import json
import re
from v31_rotation_ledger import stage, validate_state
from v31_second_resume_safe import validate_persisted_pair, decide_resume

REPO = 'adelrib27/blogger-automation1'
BRANCH = 'lab/v31r1-shopee-safe-20261103'
BLOG_ID = '4739187376492839837'
PAGE_ID = '2446067640331732447'
CATEGORIES = ('Decoração', 'Organização', 'Cozinha', 'Quarto')
START = '<!-- UNIVERSAL_V31_STORE_AUTO_START -->'
END = '<!-- UNIVERSAL_V31_STORE_AUTO_END -->'

class ReservationBlocked(ValueError):
    pass

def require(condition, message):
    if not condition:
        raise ReservationBlocked(message)

def is_git_sha(value):
    return isinstance(value, str) and re.fullmatch('[0-9a-f]{40}', value) is not None

def is_sha256(value):
    return isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value) is not None

def git_blob_sha(content: bytes) -> str:
    require(type(content) is bytes, 'Git blob exige bytes imutaveis')
    header = b'blob ' + str(len(content)).encode('ascii') + b'\0'
    return sha1(header + content).hexdigest()

def require_cas(*, expected_head: str, observed_head: str,
                expected_ledger_blob: str, ledger_bytes: bytes,
                expected_history_blob: str, history_bytes: bytes) -> None:
    """Offline CAS fence. External reader must supply authenticated remote values."""
    require(is_git_sha(expected_head) and is_git_sha(observed_head), 'Git HEAD invalido')
    require(expected_head == observed_head, 'Git HEAD alterado: conflito CAS')
    require(is_git_sha(expected_ledger_blob) and is_git_sha(expected_history_blob),
            'Git blob pin invalido')
    require(git_blob_sha(ledger_bytes) == expected_ledger_blob, 'Ledger remoto mudou')
    require(git_blob_sha(history_bytes) == expected_history_blob, 'Historico remoto mudou')

def decode_json(content: bytes, name: str) -> dict:
    require(type(content) is bytes and 0 < len(content) < 1024 * 1024, name + ' nao confiavel')
    try:
        obj = json.loads(content.decode('utf-8'))
    except (UnicodeError, ValueError) as e:
        raise ReservationBlocked(name + ' nao e JSON UTF8') from e
    require(type(obj) is dict, name + ' raiz nao e objeto')
    return obj

def pinned_profile(profile: dict, repository: str, branch: str) -> None:
    require(repository == REPO and branch == BRANCH, 'Repositorio/branch nao autorizados')
    require(type(profile) is dict and profile.get('mode') == 'SAFE'
            and profile.get('blog_id') == BLOG_ID and profile.get('page_id') == PAGE_ID
            and profile.get('page_url') == 'https://blog-teste-tema-worpress.blogspot.com/p/loja.html',
            'Perfil LAB divergente')
    require(tuple(profile.get('categories', [])) == CATEGORIES
            and profile.get('expected_products') == 16
            and profile.get('per_category') == {c: 4 for c in CATEGORIES},
            'Distribuicao de produtos divergente')

def selection_ids(selection_bytes: bytes, profile: dict) -> tuple[str, list[str]]:
    doc = decode_json(selection_bytes, 'Selecao Shopee')
    require(doc.get('schemaVersion') == 1 and doc.get('status') == 'SAFE_READY'
            and doc.get('publishReady') is True and doc.get('dryRun') is True
            and doc.get('blogId') == profile['blog_id'], 'Selecao nao e SAFE da LOJA LAB')
    require(doc.get('totalItems') == 16 and doc.get('uniqueItemIds') == 16, 'Selecao nao contem 16 unicos')
    gates = doc.get('gates', {})
    require(type(gates) is dict and all(gates.get(k) is True for k in (
        'allLinksResolved', 'semanticRulesApplied', 'finalProductGate',
        'failClosed', 'allPhotosPresent', 'expectedCategories', 'expectedItems')),
        'Gates comerciais incompletos')
    groups = doc.get('categories')
    require(type(groups) is dict and tuple(groups) == CATEGORIES, 'Categorias Shopee divergentes')
    ids = []
    for cat in CATEGORIES:
        records = groups[cat]
        require(type(records) is list and len(records) == 4, 'Quatro produtos por categoria exigidos')
        for product in records:
            require(type(product) is dict and product.get('category') == cat, 'Produto/categoria invalido')
            ident = str(product.get('itemId', ''))
            require(re.fullmatch(r'[0-9]{4,25}', ident) is not None, 'Item ID invalido')
            require(isinstance(product.get('imageUrl'), str) and product['imageUrl'].startswith('https://')
                    and isinstance(product.get('affiliateUrl'), str)
                    and product['affiliateUrl'].startswith('https://s.shopee.com.br/'),
                    'Imagem/afiliado ausente ou nao validado')
            ids.append(ident)
    require(len(set(ids)) == 16, 'Itens repetidos dentro da selecao')
    return sha256(selection_bytes).hexdigest(), ids

def check_html(before: bytes, after: bytes, selected_ids: list[str]) -> tuple[str, str]:
    require(type(before) is bytes and type(after) is bytes and 1000 < len(before) < 180000
            and 1000 < len(after) < 180000 and before != after, 'HTML original/candidato invalido')
    try:
        old, new = before.decode('utf-8'), after.decode('utf-8')
    except UnicodeError as e:
        raise ReservationBlocked('HTML nao e UTF8') from e
    for html in (old, new):
        require(html.count(START) == html.count(END) == 1, 'Marcadores V31 ausentes/duplicados')
        require(html.index(START) < html.index(END), 'Ordem dos marcadores incorreta')
        require(html.count('id="cp-loja"') == 1, 'Raiz da LOJA alterada')
        require(html.count('class="ub-product-card"') == 16
                and html.count('class="ub-product-image"') == 16
                and html.count('class="ub-product-action"') == 16,
                'Cards/fotos/botoes da LOJA incompletos')
        require(html.count('href="https://s.shopee.com.br/') == 16,
                'Links de afiliado da LOJA incompletos')
        require('<script' not in html.lower(), 'Script injetado na Page LOJA')
    # O tema, a navegacao e a divulgacao externa aos marcadores sao imutaveis.
    old_prefix, old_suffix = old.split(START, 1)[0], old.split(END, 1)[1]
    new_prefix, new_suffix = new.split(START, 1)[0], new.split(END, 1)[1]
    require((old_prefix, old_suffix) == (new_prefix, new_suffix),
            'HTML fora da regiao atualizavel mudou')
    observed_ids = re.findall(r'data-item-id=["\']([0-9]+)["\']', new)
    require(observed_ids == selected_ids, 'HTML candidato difere da selecao Shopee')
    old_ids = re.findall(r'data-item-id=["\']([0-9]+)["\']', old)
    require(len(old_ids) == len(set(old_ids)) == 16, 'Pagina original invalida')
    require(not (set(old_ids) & set(observed_ids)), 'Nova vitrine repete produtos da primeira')
    return sha256(before).hexdigest(), sha256(after).hexdigest()

def prepare_reservation(*, repository: str, branch: str, profile: dict,
                        ledger_bytes: bytes, history_bytes: bytes,
                        selection_bytes: bytes, blogger_html_bytes: bytes,
                        candidate_html_bytes: bytes, expected_head: str,
                        observed_head: str, expected_ledger_blob: str,
                        expected_history_blob: str) -> dict:
    """Generate a *proposed* PLAN; never persists it, grants publication or modifies inputs."""
    pinned_profile(profile, repository, branch)
    require_cas(expected_head=expected_head, observed_head=observed_head,
                expected_ledger_blob=expected_ledger_blob, ledger_bytes=ledger_bytes,
                expected_history_blob=expected_history_blob, history_bytes=history_bytes)
    state, history = decode_json(ledger_bytes, 'Ledger'), decode_json(history_bytes, 'Historico')
    validate_persisted_pair(state, history)
    require(state['blogId'] == BLOG_ID and state['pageId'] == PAGE_ID, 'Ledger de outro alvo')
    require(all(op['status'] == 'PERSISTED' for op in state['operations']),
            'Existe transacao anterior nao concluida')
    selection_sha, ids = selection_ids(selection_bytes, profile)
    historical = [str(x.get('itemId')) for run in history['runs'] for x in run.get('items', [])]
    require(len(historical) == len(set(historical)), 'Historico ja contem IDs duplicados')
    require(not set(ids).intersection(historical), 'Selecao reutiliza IDs do historico')
    original_sha, candidate_sha = check_html(blogger_html_bytes, candidate_html_bytes, ids)
    proposed = stage(state, selection_sha, original_sha, candidate_sha)
    validate_state(proposed)
    require(len(proposed['operations']) == len(state['operations']) + 1
            and proposed['operations'][-1]['status'] == 'PLAN', 'Reserva nao unica')
    output = (json.dumps(proposed, sort_keys=True, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    return {
        'status': 'V31_LAB_PROPOSED_GIT_RESERVATION_OFFLINE',
        'operation_id': proposed['operations'][-1]['operationId'],
        'selection_sha256': selection_sha, 'original_html_sha256': original_sha,
        'candidate_html_sha256': candidate_sha, 'expected_parent_head': expected_head,
        'expected_ledger_blob': expected_ledger_blob,
        'expected_history_blob': expected_history_blob,
        'proposed_ledger_blob': git_blob_sha(output),
        'proposed_ledger_bytes': output,
        'unchanged_history_blob': git_blob_sha(history_bytes),
        'items': len(ids), 'git_write_allowed': False,
        'blogger_put_allowed': False, 'cron_allowed': False,
    }

def inspect_committed_reservation(*, reservation: dict, committed_ledger_bytes: bytes,
                                  committed_history_bytes: bytes, parent_head: str,
                                  reservation_commit_head: str, observed_remote_head: str,
                                  observed_blogger_html_bytes: bytes) -> dict:
    """Offline readback classification. Parent/head must be authenticated externally."""
    require(is_git_sha(parent_head) and parent_head == reservation.get('expected_parent_head'),
            'Parent Git divergente da reserva')
    require(is_git_sha(reservation_commit_head) and reservation_commit_head == observed_remote_head,
            'Reserva Git ausente ou ultrapassada por outra escrita')
    require(git_blob_sha(committed_ledger_bytes) == reservation.get('proposed_ledger_blob'),
            'Reserva nao persistida exatamente no ledger')
    require(git_blob_sha(committed_history_bytes) == reservation.get('expected_history_blob'),
            'Historico alterado enquanto aguardava reserva')
    state = decode_json(committed_ledger_bytes, 'Ledger reservado')
    history = decode_json(committed_history_bytes, 'Historico reservado')
    require(type(observed_blogger_html_bytes) is bytes, 'Readback Blogger ausente')
    decision = decide_resume(state=state, history=history,
                             blog_id=BLOG_ID, page_id=PAGE_ID,
                             selection_sha=reservation['selection_sha256'],
                             observed_html_sha=sha256(observed_blogger_html_bytes).hexdigest())
    return {
        'status': 'V31_LAB_RESERVED_READBACK_CLASSIFIED_OFFLINE',
        'decision': decision['decision'], 'operation_id': decision['operationId'],
        'blogger_put_allowed': False, 'git_write_allowed': False,
        'cron_allowed': False,
    }
