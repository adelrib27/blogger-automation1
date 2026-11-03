#!/usr/bin/env python3
from __future__ import annotations

from http import HTTPStatus

import blog_id_url_resilience_v07 as blog_id_url_resilience
import local_service_v05 as v05
import new_blog_selector_resilience as new_blog_selector_resilience
import provision_new_blog_v20 as provision
import timezone_resilience_v07 as timezone_resilience
import timezone_keyboard_resilience_v07 as timezone_keyboard_resilience
import timezone_offscreen_resilience_v07 as timezone_offscreen_resilience
import timezone_virtual_window_resilience_v07 as timezone_virtual_window_resilience
import timezone_physical_click_resilience_v07 as timezone_physical_click_resilience

new_blog_selector_resilience.install()
blog_id_url_resilience.install()
timezone_resilience.install()
timezone_keyboard_resilience.install()
timezone_offscreen_resilience.install()
timezone_virtual_window_resilience.install()
timezone_physical_click_resilience.install()


class Handler(v05.Handler):
    server_version = "BloggerLocalRunner/0.7"

    def do_GET(self) -> None:
        if self.path != "/v1/health":
            return super().do_GET()
        if not self._require_auth():
            return
        self._send(
            HTTPStatus.OK,
            {
                "ok": True,
                "service": "blogger-local-runner",
                "version": "0.7",
                "bind": "loopback",
                "capabilities": ["create", "settings", "v20", "provision-new-blog-v20"],
            },
        )

    def do_POST(self) -> None:
        if self.path != "/v1/provision-new-blog-v20":
            return super().do_POST()
        if not self._require_auth():
            return
        try:
            payload = self._read_json()
        except ValueError as exc:
            self._send(HTTPStatus.BAD_REQUEST, {"ok": False, "error": "bad_request", "message": str(exc)})
            return

        confirm = str(payload.get("confirm") or "")
        if confirm != provision.CONFIRMATION:
            self._send(
                HTTPStatus.BAD_REQUEST,
                {
                    "ok": False,
                    "error": "confirmation_required",
                    "message": f'Use confirm="{provision.CONFIRMATION}".',
                },
            )
            return

        self._run_exclusive(
            lambda: provision.execute_provision(
                str(payload.get("title") or ""),
                str(payload.get("address") or ""),
                str(payload.get("description") or ""),
                str(payload.get("search_description") or ""),
                timezone=str(payload.get("timezone") or v05.base.DEFAULT_TIMEZONE) if hasattr(v05.base, "DEFAULT_TIMEZONE") else str(payload.get("timezone") or provision.settings.DEFAULT_TIMEZONE),
                palette=str(payload.get("palette") or "auto"),
                confirm=confirm,
                cdp_url=v05.base._cdp_url(),
                diagnostics_dir=v05.base._diagnostics_dir(),
            )
        )


def main() -> int:
    v05.base._required_token()
    host = v05.base.DEFAULT_HOST
    port = v05.base._env_port()
    server = v05.base.ThreadingHTTPServer((host, port), Handler)
    print(f"Blogger local runner v0.7 ativo em http://{host}:{port}")
    print("Auto-start compatível; provisionamento novo blog V20 disponível.")
    print("Chrome/CDP continua loopback; resiliência de criação e proteções V20 preservadas.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
