"""robots.txt per RFC 9309, and redirects checked hop by hop — the PR #703 review finding O22
(`docs/records/2026-10-14-theme-intelligence-open-review-findings.md`).

`urllib.robotparser` read every rule as a plain prefix, so `*` and `$` patterns never matched:
J.P. Morgan's `Disallow: /*.pdf` allowed every PDF outside `/content`. And the HTTP client
followed redirects itself, so a redirect to another host — or to a disallowed path — was fetched
without that host's robots.txt ever being read.

The J.P. Morgan file is the REAL robots.txt of privatebank.jpmorgan.com as probed by this tool
(`fixtures/theme_intelligence/robots/`). Hosts in the fetch tests are `.test` stand-ins.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import httpx
import pytest

from tests.theme_intelligence_support import FIXTURES
from vinci.theme_intelligence.config import USER_AGENT
from vinci.theme_intelligence.fetch import MAX_REDIRECTS, PoliteFetcher, RobotsRules
from vinci.theme_intelligence.schemas import RetrievalState

PRODUCT = USER_AGENT.split("/", 1)[0]
JPM = (FIXTURES / "robots" / "privatebank_jpmorgan_com.txt").read_text()
JPM_HOST = "https://privatebank.jpmorgan.com"


# --- the rules ---------------------------------------------------------------------------------

@pytest.mark.parametrize(("path", "allowed"), [
    ("/apac/en/insights/markets-and-investing/tmt/outlook-2027.pdf", False),  # Disallow /*.pdf
    ("/apac/en/insights/x.pdf?download=1", False),
    ("/apac/en/insights/markets-and-investing/tmt/a/jcr_content/par", False),  # */jcr_content/*
    ("/apac/en/insights/thank-you", False),  # */thank-you
    ("/content/dam/jpm-pb-aem/global/en/documents/x.pdf", False),  # a plain prefix, as before
    ("/apac/en/insights/markets-and-investing/tmt/a-calm-index", True),  # an article
    ("/etc/clientlibs/site.css", True),  # Allow /*.css
])
def test_the_real_jpm_robots_txt_is_read_with_its_wildcards(path: str, allowed: bool) -> None:
    assert RobotsRules.parse(JPM, PRODUCT).allows(JPM_HOST + path) is allowed


def test_the_most_specific_rule_decides_and_allow_wins_a_tie() -> None:
    r = RobotsRules.parse("User-agent: *\nDisallow: /research\nAllow: /research/public\n"
                          "Disallow: /tie\nAllow: /tie\nDisallow: /*.php$\n", PRODUCT)
    assert not r.allows("https://h.test/research/private")
    assert r.allows("https://h.test/research/public/note")  # the longer Allow
    assert r.allows("https://h.test/tie")  # equal length: Allow
    assert not r.allows("https://h.test/a/b.php")  # `$`: the path ends there …
    assert r.allows("https://h.test/a/b.php?x=1")  # … or the rule does not match
    assert r.allows("https://h.test/anything-else")


def test_our_own_group_replaces_the_star_group_and_matches_case_insensitively() -> None:
    text = (f"User-agent: *\nDisallow: /\nCrawl-delay: 9\n\nUser-agent: {PRODUCT.upper()}\n"
            f"Disallow: /private\n")
    r = RobotsRules.parse(text, PRODUCT)
    assert r.allows("https://h.test/research") and not r.allows("https://h.test/private/x")
    assert r.crawl_delay == 9.0  # our group states none: the `*` group's
    other = RobotsRules.parse(text, "another-crawler")
    assert not other.allows("https://h.test/research")
    # an empty Disallow restricts nothing; a rule before any User-agent belongs to no group
    assert RobotsRules.parse("Disallow: /\nUser-agent: *\nDisallow:\n", PRODUCT).allows(
        "https://h.test/x")


# --- the fetcher -------------------------------------------------------------------------------

class Web:
    """url -> (status, body[, headers]); unknown URLs answer 404. Logs every request."""

    def __init__(self, pages: dict[str, Any]) -> None:
        self.pages = pages
        self.log: list[str] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        self.log.append(url)
        status, body, *rest = self.pages.get(url, (404, ""))
        headers = {"content-type": "text/html", **(rest[0] if rest else {})}
        return httpx.Response(status, text=body, headers=headers, request=request)


def _fetcher(tmp: Path, web: Web) -> PoliteFetcher:
    client = httpx.Client(transport=httpx.MockTransport(web), follow_redirects=True,
                          headers={"User-Agent": USER_AGENT})
    return PoliteFetcher(tmp / "http", min_delay_s=0.0, max_retries=0, client=client)


PAGE = "<html><body><p>[HYPOTHETICAL] text</p></body></html>"


def test_a_wildcard_rule_keeps_the_fetcher_off_the_page(tmp_path: Path) -> None:
    web = Web({"https://pub.test/robots.txt": (200, "User-agent: *\nDisallow: /*.pdf\n"),
               "https://pub.test/notes/report.pdf": (200, "%PDF"),
               "https://pub.test/notes/report": (200, PAGE)})
    f = _fetcher(tmp_path, web)
    res = f.fetch("https://pub.test/notes/report.pdf")
    assert res.state is RetrievalState.BLOCKED and "robots.txt disallows" in res.note
    assert "https://pub.test/notes/report.pdf" not in web.log
    assert f.fetch("https://pub.test/notes/report").state is RetrievalState.FULL


def test_a_redirect_to_a_host_whose_robots_txt_disallows_it_is_not_followed(
        tmp_path: Path) -> None:
    web = Web({"https://pub.test/robots.txt": (404, ""),
               "https://pub.test/a": (302, "", {"location": "https://other.test/a"}),
               "https://other.test/robots.txt": (200, "User-agent: *\nDisallow: /\n"),
               "https://other.test/a": (200, PAGE)})
    res = _fetcher(tmp_path, web).fetch("https://pub.test/a")
    assert res.state is RetrievalState.BLOCKED
    assert "redirected to https://other.test/a" in res.note and "disallows" in res.note
    assert "https://other.test/robots.txt" in web.log  # the target host's file was read …
    assert "https://other.test/a" not in web.log  # … and its page never requested


def test_a_redirect_the_target_host_allows_is_followed_hop_by_hop(tmp_path: Path) -> None:
    web = Web({"https://pub.test/robots.txt": (404, ""),
               "https://pub.test/a": (301, "", {"location": "/b"}),
               "https://pub.test/b": (302, "", {"location": "https://other.test/c"}),
               "https://other.test/robots.txt": (200, "User-agent: *\nDisallow: /private\n"),
               "https://other.test/c": (200, PAGE)})
    f = _fetcher(tmp_path, web)
    res = f.fetch("https://pub.test/a")
    assert res.state is RetrievalState.FULL and res.final_url == "https://other.test/c"
    assert web.log == ["https://pub.test/robots.txt", "https://pub.test/a", "https://pub.test/b",
                       "https://other.test/robots.txt", "https://other.test/c"]
    assert f.stats.requests == len(web.log)  # every hop is a request, and counted


def test_each_hop_is_spaced_like_any_request_to_its_host(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from vinci.theme_intelligence import fetch as fetch_mod

    waits: list[str] = []
    web = Web({"https://pub.test/robots.txt": (404, ""),
               "https://pub.test/a": (302, "", {"location": "https://other.test/c"}),
               "https://other.test/robots.txt": (404, ""), "https://other.test/c": (200, PAGE)})
    monkeypatch.setattr(fetch_mod.time, "sleep",  # type: ignore[attr-defined]
                        lambda s: waits.append(web.log[-1]))
    client = httpx.Client(transport=httpx.MockTransport(web), headers={"User-Agent": USER_AGENT})
    f = PoliteFetcher(tmp_path / "http", min_delay_s=5.0, max_retries=0, client=client)
    assert f.fetch("https://pub.test/a").state is RetrievalState.FULL
    # each host's second request waits its spacing: the page after pub.test's robots.txt, and
    # the redirected page after other.test's
    assert waits == ["https://pub.test/robots.txt", "https://other.test/robots.txt"]


def test_a_redirect_to_a_disallowed_path_on_the_same_host_is_not_followed(
        tmp_path: Path) -> None:
    web = Web({"https://pub.test/robots.txt": (200, "User-agent: *\nDisallow: /members\n"),
               "https://pub.test/a": (302, "", {"location": "/members/a"}),
               "https://pub.test/members/a": (200, PAGE)})
    res = _fetcher(tmp_path, web).fetch("https://pub.test/a")
    assert res.state is RetrievalState.BLOCKED and "/members/a" in res.note
    assert "https://pub.test/members/a" not in web.log


def test_a_redirect_chain_stops_after_the_limit(tmp_path: Path) -> None:
    hops = {f"https://pub.test/{i}": (302, "", {"location": f"/{i + 1}"})
            for i in range(MAX_REDIRECTS + 2)}
    web = Web({"https://pub.test/robots.txt": (404, ""), **hops})
    res = _fetcher(tmp_path, web).fetch("https://pub.test/0")
    assert res.state is RetrievalState.BLOCKED and "redirects" in res.note
    assert len([u for u in web.log if not u.endswith("robots.txt")]) == MAX_REDIRECTS + 1
