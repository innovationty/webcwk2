from pathlib import Path

from search_tool.crawler import CrawlReport
from search_tool.engine import SearchEngine
from search_tool.models import CrawledPage


def test_engine_build_uses_crawler_and_persists_index(monkeypatch, tmp_path: Path) -> None:
    report = CrawlReport(
        pages=[
            CrawledPage(
                url="https://example.test/page-1",
                title="Page 1",
                text="good friends",
            )
        ]
    )

    class FakeCrawler:
        def __init__(self, start_url: str, politeness_window: float) -> None:
            self.start_url = start_url
            self.politeness_window = politeness_window

        def crawl(self) -> CrawlReport:
            return report

    monkeypatch.setattr("search_tool.engine.WebCrawler", FakeCrawler)

    engine = SearchEngine()
    crawl_report, saved_path = engine.build(
        start_url="https://example.test/",
        output_path=tmp_path / "index.json",
        politeness_window=0.0,
    )

    assert crawl_report is report
    assert saved_path.exists()
    assert engine.find("good")
    assert engine.suggest("frends") == ["friends"]

