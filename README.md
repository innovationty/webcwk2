# Coursework 2 Search Engine Tool

This project implements a command-line search tool for `https://quotes.toscrape.com/`.

## Features

- Website crawler with a 6-second politeness window between HTTP requests.
- Inverted index storing per-document term frequency and positions.
- Persistent single-file JSON index for `build` and `load` commands.
- Search shell supporting `build`, `load`, `print`, and `find`.
- Ranked retrieval using TF-IDF style scoring.
- Extra features for higher mark bands:
  - phrase queries with double quotes, for example `find "good friends"`
  - spelling suggestions for unknown terms
  - modular architecture with type hints and tests

## Installation

Create or activate a Python 3.12 environment and install dependencies:

```bash
python -m pip install -e ".[dev]"
```

On Windows PowerShell, keep the local path argument after `-e` and quote `.[dev]` exactly as shown above.

## Usage

Run the interactive shell:

```bash
python -m search_tool
```

The `build` command crawls the live target website and respects a 6-second politeness window, so a full crawl can take a long time. The shell now prints per-page crawl progress during indexing.

Available commands:

- `build` crawls the target website, builds the index, and saves it to `index/search_index.json`.
- `load` loads the existing index from disk.
- `print nonsense` prints the postings for a single term.
- `find indifference` finds ranked pages containing the term.
- `find good friends` performs an AND search across all query terms.
- `find "good friends"` performs a phrase query.
- `help` prints command help.
- `exit` quits the shell.

## Architecture

- `search_tool/crawler.py`: website crawling, request throttling, link extraction.
- `search_tool/indexer.py`: inverted index construction, query parsing, phrase matching, ranking.
- `search_tool/storage.py`: JSON serialisation for saving/loading the index.
- `search_tool/engine.py`: orchestration layer used by the CLI.
- `search_tool/cli.py`: interactive shell.

## Data structures and design rationale

- Terms are normalised to lowercase so search is case-insensitive.
- Each term maps to a postings dictionary keyed by URL.
- Each posting stores:
  - `frequency`: number of occurrences in the page
  - `positions`: token offsets used for phrase matching
- Document metadata stores title and token count, which supports ranking.
- Ranking uses a TF-IDF style score:

  - `tf = term_frequency / document_length`
  - `idf = 1 + log((N + 1) / (df + 1))`

This keeps the implementation simple while giving more relevant ordering than an unordered match list.

## Testing

Run the test suite:

```bash
pytest
```

The tests cover:

- tokenisation and normalisation
- index construction and position tracking
- multi-term AND retrieval
- phrase queries
- spelling suggestions
- save/load round trips

## Complexity notes

- Crawling is linear in the number of discovered pages and links.
- Index construction is linear in the number of tokens processed.
- Single-term lookup is effectively `O(1)` for the term dictionary plus output size.
- Multi-term search intersects posting lists, which is efficient when terms are selective.
- Phrase matching uses stored positions rather than rescanning raw page text.

## Coursework checklist mapping

- Crawling implementation: complete.
- Inverted index with statistics: complete.
- Storage and retrieval: complete.
- Search commands: complete.
- Testing and coverage: included.
- Code quality and documentation: included.
- Video and Git evidence: still to be produced by the student.

## Video points to cover

- Show `build`, `load`, `print`, and `find` live.
- Explain why postings store both frequency and positions.
- Explain TF-IDF ranking and phrase matching.
- Demonstrate tests and coverage output.
- Critically evaluate where GenAI helped and where you corrected it.
