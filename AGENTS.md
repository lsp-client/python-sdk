# AGENTS.md

## Development Commands

- Lint & format: `ruff check --fix && ruff format`
- Type checking: `ty check <dir_or_file>`
- Run tests: `uv run pytest`
- Python: always use `uv`

## Code Style Guidelines

- Python: 3.12+ required
- Types: Full type annotations required, use `lsp_client.utils.types.lsp_type` for standard LSP types
- Error handling: Must use concrete exception types
- Async: Use async/await, `asyncer.TaskGroup` for concurrency
- Structure: Follow capability-based protocol pattern in `capability/` module
