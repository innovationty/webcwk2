from pathlib import Path

from search_tool.engine import SearchEngine
from search_tool.indexer import InvertedIndex
from search_tool.models import CrawledPage
from search_tool.storage import load_index, save_index


def test_save_and_load_round_trip(tmp_path: Path) -> None:
    pages = [
        CrawledPage(
            url="https://example.test/page-1",
            title="Page 1",
            text="Indifference is expensive.",
        )
    ]
    index = InvertedIndex.from_pages(pages)

    path = save_index(index, tmp_path / "search_index.json")
    loaded = load_index(path)

    assert loaded.get_postings("indifference")


def test_engine_requires_index_before_search() -> None:
    engine = SearchEngine()

    try:
        engine.find("anything")
    except RuntimeError as exc:
        assert "build" in str(exc).lower()
    else:
        raise AssertionError("Expected RuntimeError when index is not loaded")


def test_engine_requires_index_before_print_and_suggest() -> None:
    engine = SearchEngine()

    for action in (lambda: engine.print_term("anything"), lambda: engine.suggest("anything")):
        try:
            action()
        except RuntimeError as exc:
            assert "build" in str(exc).lower()
        else:
            raise AssertionError("Expected RuntimeError when index is not loaded")


def test_engine_load_and_print_term(tmp_path: Path) -> None:
    pages = [
        CrawledPage(
            url="https://example.test/page-1",
            title="Page 1",
            text="Nonsense stays nonsense.",
        )
    ]
    index = InvertedIndex.from_pages(pages)
    path = save_index(index, tmp_path / "search_index.json")

    engine = SearchEngine()
    engine.load(path)

    postings = engine.print_term("nonsense")
    assert "https://example.test/page-1" in postings