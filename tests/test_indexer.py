from search_tool.indexer import InvertedIndex, tokenize
from search_tool.models import CrawledPage


def build_index() -> InvertedIndex:
    return InvertedIndex.from_pages(
        [
            CrawledPage(
                url="https://example.test/page-1",
                title="Page 1",
                text="Good friends show good character and good judgement.",
            ),
            CrawledPage(
                url="https://example.test/page-2",
                title="Page 2",
                text="Friends value honesty and character.",
            ),
            CrawledPage(
                url="https://example.test/page-3",
                title="Page 3",
                text="Nonsense is still nonsense.",
            ),
        ]
    )


def test_tokenize_is_case_insensitive() -> None:
    assert tokenize("Good, good! FRIENDS") == ["good", "good", "friends"]


def test_postings_store_frequency_and_positions() -> None:
    index = build_index()
    postings = index.get_postings("good")

    assert postings["https://example.test/page-1"]["frequency"] == 3
    assert postings["https://example.test/page-1"]["positions"] == [0, 3, 6]


def test_find_returns_and_matches() -> None:
    index = build_index()
    results = index.search("good friends")

    assert [result.url for result in results] == ["https://example.test/page-1"]


def test_phrase_query_requires_adjacent_terms() -> None:
    index = build_index()
    results = index.search('"good friends"')

    assert [result.url for result in results] == ["https://example.test/page-1"]
    assert index.search('"friends good"') == []


def test_suggest_returns_close_match() -> None:
    index = build_index()
    assert "friends" in index.suggest("frends")
