# Configuration Management

The `lsp-client` SDK provides a robust and flexible way to manage Language Server Protocol (LSP) configurations. It supports global settings, path-based overrides, and automatic synchronization with the server.

## Default Configurations

**All built-in clients now come with sensible default configurations that enable extra features out of the box**, including:
- **Inlay hints** for types, parameters, return values, etc.
- **Enhanced diagnostics** and linting
- **Auto-import completions**
- **Code lenses** and other IDE features

This means you can start using clients immediately without needing to manually configure these features. The defaults are automatically applied when the client starts, unless you provide your own `configuration_map`.

### Example: Using Default Configuration

```python
from lsp_client.clients.rust_analyzer import RustAnalyzerClient

# Simply create and use the client - inlay hints and other features are enabled by default
async with RustAnalyzerClient() as client:
    hints = await client.request_inlay_hint(file_path="main.rs", range=...)
    # Inlay hints are automatically enabled without any configuration!
```

### Customizing Default Configuration

You can still provide your own configuration to override or extend the defaults:

```python
from lsp_client.utils.config import ConfigurationMap
from lsp_client.clients.pyright import PyrightClient

# Create custom configuration
config_map = ConfigurationMap()
config_map.update_global({
    "python": {
        "analysis": {
            "typeCheckingMode": "strict",  # Override default
            "autoImportCompletions": False,  # Disable a feature
        }
    }
})

# Apply custom configuration
async with PyrightClient() as client:
    client.configuration_map = config_map
    # Now uses your custom settings instead of defaults
```

## ConfigurationMap

The `ConfigurationMap` is the central utility for managing settings. It implements a tiered configuration logic similar to "User Settings" vs. "Workspace Settings" in popular IDEs.

### Core Features

- **Global Config**: Default settings applied to all files.
- **Scoped Overrides**: High-priority settings applied to files matching specific Glob patterns (e.g., `**/tests/**`).
- **Deep Merging**: Nested dictionaries are merged recursively, ensuring that partial updates don't wipe out unrelated settings.
- **Auto-Sync**: Automatically notifies the server when configurations change.

### Basic Usage

```python
from lsp_client.utils.config import ConfigurationMap
from lsp_client.clients.pyright import PyrightClient

# 1. Initialize the map
config_map = ConfigurationMap()

# 2. Set global configurations
config_map.update_global({
    "python": {
        "analysis": {
            "typeCheckingMode": "basic",
            "autoImportCompletions": True
        }
    }
})

# 3. Add path-specific overrides
# For example, disable type checking for the tests directory
config_map.add_scope(
    pattern="**/tests/**",
    config={
        "python": {
            "analysis": {
                "typeCheckingMode": "off"
            }
        }
    }
)
```

## Integrating with the Client

To enable configuration support, assign your `config_map` to the client's `configuration_map` attribute.

```python
async with PyrightClient(workspace=Path.cwd()) as client:
    client.configuration_map = config_map
    # The SDK will now handle 'workspace/configuration' requests automatically
```

## Automatic Synchronization

One of the most powerful features is **Automatic Sync**. If your client supports the `workspace/didChangeConfiguration` capability (standard in most built-in clients like `PyrightClient`), the SDK will automatically notify the server whenever you update the `ConfigurationMap`.

### How it Works

1. You update the `config_map` using `update_global` or `add_scope`.
2. The SDK detects the change and sends a `workspace/didChangeConfiguration` notification to the server.
3. The server, upon receiving the notification, typically clears its cache and requests fresh configuration from the client.

```python
# Updating config at runtime
config_map.update_global({"python.analysis.typeCheckingMode": "strict"})

# The server is automatically notified and will see the "strict" mode immediately.
```

## Advanced: Change Listeners

You can register custom listeners to react to configuration changes. Listeners must follow the `ConfigurationChangeListener` protocol.

```python
def my_listener(config_map, **kwargs):
    reason = kwargs.get("reason", "unknown")
    print(f"Config changed! Reason: {reason}")

config_map.on_change(my_listener)

# Pass context to your listeners
config_map.update_global({"setting": True}, reason="User Preference Update")
```

## Implementation Details

### Merge Strategy
When a file matches multiple scope patterns, configurations are merged in the order they were added. The merge is **deep**, meaning:

```python
# Base
{"a": {"b": 1, "c": 2}}
# Update
{"a": {"b": 3}}
# Result
{"a": {"b": 3, "c": 2}}  # "c" is preserved
```

### Path Resolution
The `scope_uri` provided by the server is automatically converted to a local filesystem path before pattern matching, allowing you to use standard Glob patterns.

## Default Configurations by Client

Each built-in client provides default configurations tailored to the language server's capabilities:

### Rust Analyzer
- Inlay hints: Types, parameters, lifetimes, closures, reborrow hints
- Diagnostics: Enabled with experimental features
- Completion: Auto-import, auto-self, callable snippets
- Check on save: Enabled
- Code lenses: Run, debug, implementations, references

### Gopls (Go)
- Inlay hints: All types (variables, parameters, function types, etc.)
- Code lenses: Generate, test, tidy, upgrade dependencies, vulnerability checks
- Analyses: Field alignment, nilness, unused params/writes
- Completion: Documentation, deep completion, fuzzy matching, placeholders
- Semantic tokens: Enabled

### Pyright (Python)
- Inlay hints: Variable types, function return types, call arguments, pytest parameters
- Auto-import completions: Enabled
- Type checking mode: Basic (can be overridden)
- Diagnostics: Open files only
- Auto-search paths and indexing: Enabled

### Basedpyright (Python)
- Inlay hints: Variable types, function return types, call arguments, pytest parameters
- Auto-import completions: Enabled
- Type checking mode: Recommended (can be overridden)
- Diagnostics: Open files only
- Auto-search paths and indexing: Enabled

### TypeScript Language Server
- Inlay hints: All types for both TypeScript and JavaScript
- Suggestions: Auto-imports, complete function calls, module exports
- Preferences: Package.json auto-imports, shortest import specifier

### Deno
- Inlay hints: All parameter and type hints
- Linting: Enabled
- Unstable features: Enabled
- Code lenses: Implementations, references, tests
- Import suggestions: Auto-discover from deno.land and esm.sh

### Pyrefly (Python)
- Inlay hints: Variable types, function return types, parameter types
- Diagnostics and auto-imports: Enabled

### Ty (Python)
- Diagnostics and auto-imports: Enabled

You can always inspect the default configuration for any client:

```python
from lsp_client.clients.rust_analyzer import RustAnalyzerClient

client = RustAnalyzerClient()
config_map = client.create_default_configuration_map()

# Check if configuration exists
if config_map and config_map.has_global_config():
    # Get specific configuration values
    inlay_hints_enabled = config_map.get(None, "rust-analyzer.inlayHints.enable")
    print(f"Inlay hints enabled: {inlay_hints_enabled}")
    
    # Get entire section
    all_inlay_hints = config_map.get(None, "rust-analyzer.inlayHints")
    print(f"All inlay hint settings: {all_inlay_hints}")
```
