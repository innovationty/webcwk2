from types import SimpleNamespace

import requests

from search_tool.crawler import WebCrawler


def test_extract_links_keeps_same_domain_only() -> None:
    crawler = WebCrawler(start_url="https://quotes.toscrape.com/")
    html = """
    <html>
      <head><title>Quotes</title></head>
      <body>
        <a href="/page/2/">Next</a>
        <a href="https://quotes.toscrape.com/tag/love/">Tag</a>
        <a href="https://example.com/">External</a>
      </body>
    </html>
    """

    page = crawler._parse_page("https://quotes.toscrape.com/", html, 200)

    assert page.title == "Quotes"
    assert page.links == [
        "https://quotes.toscrape.com/page/2/",
        "https://quotes.toscrape.com/tag/love/",
    ]


def test_get_respects_politeness_window(monkeypatch) -> None:
    calls: list[str] = []
    sleeps: list[float] = []
    monotonic_values = iter([10.0, 12.0, 16.0])

    class FakeSession:
        headers = {}

        def get(self, url: str, timeout: float):
            calls.append(url)
            return SimpleNamespace(status_code=200, text="ok")

    monkeypatch.setattr("search_tool.crawler.time.monotonic", lambda: next(monotonic_values))
    monkeypatch.setattr("search_tool.crawler.time.sleep", lambda seconds: sleeps.append(seconds))

    crawler = WebCrawler(
        start_url="https://quotes.toscrape.com/",
        politeness_window=6.0,
        session=FakeSession(),
    )

    crawler._get("https://quotes.toscrape.com/")
    crawler._get("https://quotes.toscrape.com/page/2/")

    assert calls == [
        "https://quotes.toscrape.com/",
        "https://quotes.toscrape.com/page/2/",
    ]
    assert sleeps == [4.0]


def test_crawl_collects_pages_and_records_errors(monkeypatch) -> None:
    crawler = WebCrawler(start_url="https://quotes.toscrape.com/", politeness_window=0.0)

    responses = {
        "https://quotes.toscrape.com/": SimpleNamespace(
            text='<html><head><title>Home</title></head><body><a href="/page/2/">Next</a></body></html>',
            status_code=200,
            raise_for_status=lambda: None,
        )
    }

    def fake_get(url: str):
        if url in responses:
            return responses[url]
        raise requests.RequestException("boom")

    monkeypatch.setattr(crawler, "_get", fake_get)

    report = crawler.crawl()

    assert [page.url for page in report.pages] == ["https://quotes.toscrape.com/"]
    assert "https://quotes.toscrape.com/page/2/" in report.errors
