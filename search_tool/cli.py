from __future__ import annotations

import shlex
from pathlib import Path

from .engine import SearchEngine
from .storage import DEFAULT_INDEX_PATH


HELP_TEXT = """Commands:
  build              Crawl the website and save the index.
  load               Load an existing index from disk.
  print <word>       Print postings for one word.
  find <query>       Search the index. Use quotes for phrase search.
  help               Show this help text.
  exit               Quit the shell.
"""


class SearchShell:
    def __init__(self) -> None:
        self.engine = SearchEngine()

    def run(self) -> int:
        print("Search Tool Shell")
        print("Type 'help' for available commands.")

        while True:
            try:
                line = input("> ").strip()
            except EOFError:
                print()
                return 0
            except KeyboardInterrupt:
                print("\nInterrupted.")
                return 130

            if not line:
                continue

            command, *args = shlex.split(line)
            command = command.lower()

            try:
                if command == "build":
                    self._handle_build()
                elif command == "load":
                    self._handle_load()
                elif command == "print":
                    self._handle_print(args)
                elif command == "find":
                    self._handle_find(args)
                elif command == "help":
                    print(HELP_TEXT)
                elif command in {"exit", "quit"}:
                    return 0
                else:
                    print(f"Unknown command: {command}")
            except RuntimeError as exc:
                print(exc)

    def _handle_build(self) -> None:
        print("Building index. This respects the 6-second politeness window and may take time.")
        report, path = self.engine.build(
            output_path=DEFAULT_INDEX_PATH,
            on_page_crawled=self._report_build_progress,
        )
        print(f"Indexed {len(report.pages)} pages and saved to {path}.")
        if report.errors:
            print(f"Completed with {len(report.errors)} crawl errors.")

    def _report_build_progress(
        self,
        url: str,
        title: str,
        crawled_count: int,
        queued_count: int,
    ) -> None:
        print(
            f"Crawled page {crawled_count} | queued={queued_count} | title={title} | url={url}",
            flush=True,
        )

    def _handle_load(self) -> None:
        path = Path(DEFAULT_INDEX_PATH)
        self.engine.load(path)
        print(f"Loaded index from {path}.")

    def _handle_print(self, args: list[str]) -> None:
        if len(args) != 1:
            print("Usage: print <word>")
            return

        postings = self.engine.print_term(args[0])
        if not postings:
            print("No postings found.")
            return

        for url, details in postings.items():
            frequency = details["frequency"]
            positions = details["positions"]
            print(f"{url} -> frequency={frequency}, positions={positions}")

    def _handle_find(self, args: list[str]) -> None:
        if not args:
            print("Usage: find <query>")
            return

        query = " ".join(args)
        results = self.engine.find(query)
        if not results:
            suggestions = self.engine.suggest(query)
            print("No matches found.")
            if suggestions:
                print(f"Did you mean: {', '.join(suggestions)}?")
            return

        for rank, result in enumerate(results, start=1):
            print(f"{rank}. {result.title} | {result.url} | score={result.score:.4f}")


def main() -> int:
    shell = SearchShell()
    return shell.run()
