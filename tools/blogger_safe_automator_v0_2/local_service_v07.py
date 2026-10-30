#!/usr/bin/env python3
from __future__ import annotations

from http import HTTPStatus

import local_service_v06 as v06
import provision_new_blog_v20 as provision


class Handler(v06.Handler):
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
                timezone=str(payload.get("timezone") or v06.v05.base.DEFAULT_TIMEZONE) if hasattr(v06.v05.base, "DEFAULT_TIMEZONE") else str(payload.get("timezone") or provision.settings.DEFAULT_TIMEZONE),
                palette=str(payload.get("palette") or "auto"),
                confirm=confirm,
                cdp_url=v06.v05.base._cdp_url(),
                diagnostics_dir=v06.v05.base._diagnostics_dir(),
            )
        )


def main() -> int:
    v06.v05.base._required_token()
    host = v06.v05.base.DEFAULT_HOST
    port = v06.v05.base._env_port()
    server = v06.v05.base.ThreadingHTTPServer((host, port), Handler)
    print(f"Blogger local runner v0.7 ativo em http://{host}:{port}")
    print("Auto-start compatível; provisionamento novo blog V20 disponível.")
    print("Chrome/CDP continua loopback; proteções v0.6/v0.5 preservadas.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
