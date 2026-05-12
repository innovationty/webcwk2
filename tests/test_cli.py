from pathlib import Path

from search_tool.cli import SearchShell
from search_tool.models import SearchResult


def test_shell_help_then_exit(monkeypatch, capsys) -> None:
    commands = iter(["help", "exit"])
    monkeypatch.setattr("builtins.input", lambda _: next(commands))

    shell = SearchShell()
    result = shell.run()

    output = capsys.readouterr().out
    assert result == 0
    assert "Commands:" in output


def test_shell_print_without_index(monkeypatch, capsys) -> None:
    commands = iter(["print nonsense", "exit"])
    monkeypatch.setattr("builtins.input", lambda _: next(commands))

    shell = SearchShell()
    shell.run()

    output = capsys.readouterr().out
    assert "build" in output.lower()


def test_handle_print_and_find_outputs(monkeypatch, capsys) -> None:
    shell = SearchShell()

    monkeypatch.setattr(
        shell.engine,
        "print_term",
        lambda term: {
            "https://example.test/page-1": {"frequency": 2, "positions": [1, 4]}
        },
    )
    monkeypatch.setattr(
        shell.engine,
        "find",
        lambda query: [
            SearchResult(
                url="https://example.test/page-1",
                title="Page 1",
                score=1.25,
            )
        ],
    )

    shell._handle_print(["good"])
    shell._handle_find(["good", "friends"])

    output = capsys.readouterr().out
    assert "frequency=2" in output
    assert "score=1.2500" in output


def test_handle_find_shows_suggestions(monkeypatch, capsys) -> None:
    shell = SearchShell()

    monkeypatch.setattr(shell.engine, "find", lambda query: [])
    monkeypatch.setattr(shell.engine, "suggest", lambda query: ["friends"])

    shell._handle_find(["frends"])

    output = capsys.readouterr().out
    assert "Did you mean" in output


def test_handle_build_and_load(monkeypatch, capsys, tmp_path: Path) -> None:
    shell = SearchShell()
    fake_path = tmp_path / "search_index.json"

    class FakeReport:
        pages = [object(), object()]
        errors = {}

    monkeypatch.setattr(
        shell.engine,
        "build",
        lambda output_path, on_page_crawled=None: (FakeReport(), fake_path),
    )
    monkeypatch.setattr(shell.engine, "load", lambda path: object())
    monkeypatch.setattr("search_tool.cli.DEFAULT_INDEX_PATH", fake_path)

    shell._handle_build()
    shell._handle_load()

    output = capsys.readouterr().out
    assert "Indexed 2 pages" in output
    assert str(fake_path) in output
