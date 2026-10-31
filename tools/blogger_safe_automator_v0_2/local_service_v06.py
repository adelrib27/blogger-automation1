#!/usr/bin/env python3
from __future__ import annotations

# Instala primeiro o patch de resiliência no módulo browser_provision.
import browser_resilience_v06
browser_resilience_v06.install()

import local_service_v05 as v05


class Handler(v05.Handler):
    server_version = "BloggerLocalRunner/0.6"

    def do_GET(self) -> None:
        if self.path != "/v1/health":
            return super().do_GET()
        if not self._require_auth():
            return
        self._send(
            v05.HTTPStatus.OK,
            {
                "ok": True,
                "service": "blogger-local-runner",
                "version": "0.6",
                "bind": "loopback",
            },
        )


def main() -> int:
    v05.base._required_token()
    host = v05.base.DEFAULT_HOST
    port = v05.base._env_port()
    server = v05.base.ThreadingHTTPServer((host, port), Handler)
    print(f"Blogger local runner v0.6 ativo em http://{host}:{port}")
    print("Chrome oficial/CDP loopback; retry controlado para o seletor Novo blog.")
    print("V20 e proteções de Blog ID continuam herdados da v0.5.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
