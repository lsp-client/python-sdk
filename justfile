sync-pyrefly:
    rm -rf tests/assets/pyrefly tests/assets/temp_pyrefly
    git clone --depth 1 --filter=blob:none --sparse https://github.com/facebook/pyrefly tests/assets/temp_pyrefly
    cd tests/assets/temp_pyrefly && git sparse-checkout set pyrefly/lib/test/lsp
    mv tests/assets/temp_pyrefly/pyrefly/lib/test/lsp tests/assets/pyrefly
    rm -rf tests/assets/temp_pyrefly

pdoc:
    mkdir -p dist
    uv run pdoc src/lsp_client --output-dir dist --docformat google

lint path='src':
    uv run ruff check --fix {{path}}
    uv run ruff format {{path}}
    uv run ty check {{path}}

# Release a new version (e.g., just release 0.1.0)
release version:
    @echo "Releasing v{{version}}..."
    # Check if version matches pyproject.toml
    @grep -q 'version = "{{version}}"' pyproject.toml || (echo "Version mismatch in pyproject.toml"; exit 1)
    # Ensure working directory is clean
    @git diff-index --quiet HEAD || (echo "Dirty working directory, please commit or stash changes"; exit 1)
    # Run tests
    uv run pytest tests/unit tests/integration
    # Create and push tag
    git tag v{{version}}
    git push origin main
    git push origin v{{version}}
