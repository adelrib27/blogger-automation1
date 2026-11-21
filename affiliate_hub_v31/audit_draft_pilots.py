"""Conferir os rascunhos de homologação por GET nos dois CMS e SELECT no D1."""
import hashlib
import json
from pathlib import Path

from . import automatic_blogger_drafts as blogger
from . import automatic_wordpress_drafts as wordpress
from .d1_http_runner import CloudflareD1HTTPRunner
from .routing import sites


def audit():
    state = json.loads(Path(__file__).with_name("CONTINUIDADE_ESTADO.json").read_text(encoding="utf-8"))
    query = CloudflareD1HTTPRunner.from_environment()
    pilots = state["active_work"]["draft_pilots"]
    if not pilots:
        raise ValueError("draft_pilots_missing")
    for site, pilot in pilots.items():
        route = sites()[site]
        if route["publish_enabled"] is not False:
            raise ValueError("draft_route_required")
        if route["platform"] == "wordpress":
            user, password = wordpress.credentials_for(site)
            client = wordpress.WordPressRestClient(base_url=route["identifier"], username=user, application_password=password)
            client.site_settings()
            post = client.get_post(int(pilot["id"]))
            title = post["title"]["raw"]
            content = post["content"]["raw"]
        elif route["platform"] == "blogger":
            service = blogger._get_blogger_service()
            post = service.posts().get(blogId=route["identifier"], postId=pilot["id"], view="ADMIN").execute()
            if str(post["blog"]["id"]) != route["identifier"]:
                raise ValueError("blog_mismatch")
            title, content = post["title"], post["content"]
        else:
            raise ValueError("unsupported_draft_platform")
        digest = hashlib.sha256(content.encode()).hexdigest()
        if (str(post["id"]) != pilot["id"] or post["status"].lower() != "draft"
                or title != pilot["title"] or digest != pilot["html_sha256"]):
            raise ValueError("draft_readback_changed_" + site)
        jobs = query("""SELECT status FROM v31_ready_jobs
            WHERE site_key=? AND campaign=? AND html_sha256=?""", (site, route["campaign"], digest))
        if jobs != [{"status":"USED"}]:
            raise ValueError("draft_d1_mismatch_" + site)
        print(json.dumps({"site":site, "id":pilot["id"], "status":"draft", "html_sha256":digest}))


if __name__ == "__main__":
    audit()
