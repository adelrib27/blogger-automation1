"""C147 — conversão Shopee na mesma execução da verificação independente.

Somente para rota real, SKU moderado e com fonte elegível, quando não há
link da campanha no catálogo. Usa a MESMA cota D1 global da fila diária,
sem retries de mutação; persiste e relê snapshot R2 antes de liberar o SKU.

Não aprova fatos, gera textos, autoriza LIVE ou chama CMS. A indisponibilidade
de D1, Shopee, R2 ou evidência de leitura retorna bloqueio seguro.
"""
from __future__ import annotations

from pathlib import Path

from .catalog import Catalog, host_allowed
from .converter import ConversionError, convert_one
from .r2_state import verify_database
from .verified_supply import route_allows_sku


class OnDemandConversionError(ValueError):
    """Falha sanitizada e sem conteúdo remoto, URL, credenciais ou segredo."""


def convert_for_review(
    *,
    catalog: Catalog,
    storage,
    route: dict,
    product_key: str,
    app_id: str,
    app_secret: str,
    reserve_attempt,
    verification_path: Path,
) -> str:
    """Retorna CACHED, CONVERTED ou BUDGET_DENIED; nenhuma outra saída é sucesso.

    O catálogo fornecido é o snapshot oficial restaurado e exclusivo durante
    o workflow serializado. verification_path precisa apontar para um arquivo
    inexistente no mesmo diretório temporário, nunca sobrescrever o original.
    """
    if (not isinstance(route, dict)
            or route.get("publish_enabled") is not False
            or route.get("platform") not in ("blogger", "wordpress")
            or not isinstance(product_key, str)
            or not isinstance(route.get("campaign"), str)
            or not isinstance(route.get("site_key"), str)
            or not callable(reserve_attempt)):
        raise OnDemandConversionError("on_demand_route_or_budget_invalid")
    campaign = route["campaign"]
    if not isinstance(catalog, Catalog) or not route_allows_sku(catalog, route, product_key):
        raise OnDemandConversionError("on_demand_product_not_eligible")
    cached = catalog.cached_link(product_key, campaign)
    if cached is not None:
        if not host_allowed(cached, allow_short=True):
            raise OnDemandConversionError("on_demand_cached_link_untrusted")
        return "CACHED"
    if (not isinstance(app_id, str) or not app_id.strip()
            or not isinstance(app_secret, str) or not app_secret.strip()):
        raise OnDemandConversionError("on_demand_shopee_credentials_missing")
    path = Path(verification_path)
    if (path.exists() or path.is_symlink()
            or path.parent.resolve() != catalog.path.parent.resolve()
            or path == catalog.path):
        raise OnDemandConversionError("on_demand_restore_path_invalid")
    # Reserva atômica antes de QUALQUER POST. A fila regular compartilha os
    # mesmos slots globais por dia; uma falha posterior NÃO gera retry.
    try:
        reserved = reserve_attempt(campaign, product_key)
    except Exception:
        raise OnDemandConversionError("on_demand_budget_unverified") from None
    if type(reserved) is not bool:
        raise OnDemandConversionError("on_demand_budget_untrusted")
    if not reserved:
        return "BUDGET_DENIED"
    try:
        link, created = convert_one(
            catalog, product_key, campaign, app_id, app_secret)
    except (ConversionError, ValueError):
        raise OnDemandConversionError("on_demand_shopee_failed_closed") from None
    # Um replay inesperado depois da reserva não autoriza novo POST nem
    # permite tratar cache incerto como produto verificado.
    if not created or not host_allowed(link, allow_short=True):
        raise OnDemandConversionError("on_demand_conversion_receipt_invalid")
    try:
        receipt = storage.save_from(catalog.path)
        if not isinstance(receipt, dict) or receipt.get("state_saved") is not True:
            raise OnDemandConversionError("on_demand_r2_persistence_unverified")
        if storage.restore_to(path) is not True:
            raise OnDemandConversionError("on_demand_r2_restore_unverified")
        verify_database(path)
        with Catalog(path) as restored:
            remote = restored.cached_link(product_key, campaign)
            if (remote != link or not host_allowed(remote, allow_short=True)
                    or not route_allows_sku(restored, route, product_key)):
                raise OnDemandConversionError("on_demand_r2_exact_link_unverified")
    except OnDemandConversionError:
        raise
    except Exception:
        raise OnDemandConversionError("on_demand_r2_persistence_unverified") from None
    return "CONVERTED"
