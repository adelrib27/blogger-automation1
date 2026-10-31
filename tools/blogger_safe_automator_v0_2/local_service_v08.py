#!/usr/bin/env python3
from __future__ import annotations

from http import HTTPStatus

import local_service_v07 as v07


class Handler(v07.Handler):
    server_version = "BloggerLocalRunner/0.8"

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
                "version": "0.8",
                "bind": "loopback",
                "capabilities": [
                    "create",
                    "settings",
                    "v20",
                    "provision-new-blog-v20",
                    "v20-runtime-sync-guard",
                ],
            },
        )


def main() -> int:
    v07.v06.v05.base._required_token()
    host = v07.v06.v05.base.DEFAULT_HOST
    port = v07.v06.v05.base._env_port()
    server = v07.v06.v05.base.ThreadingHTTPServer((host, port), Handler)
    print(f"Blogger local runner v0.8 ativo em http://{host}:{port}")
    print("V20 protegido por sincronizacao fail-closed antes da adocao.")
    print("Chrome/CDP continua loopback; protecoes v0.7 preservadas.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
