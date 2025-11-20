# Gerrit2Git Archive

A Python tool to preserve Gerrit review history by exporting patches, generating browsable HTML documentation, and storing everything in a git repository.

## Features

- **Export Gerrit Changes**: Fetch changes from Gerrit REST API with customizable queries
- **Store Patches**: Save patches as `.patch` files (not applied, just stored)
- **Generate HTML**: Create browsable HTML pages with:
  - Change metadata (project, branch, status, owner)
  - Commit messages and file changes
  - Review labels and votes
  - Review messages and inline comments
  - Searchable index page
- **Git Repository**: Store all patches and HTML files in a git repository for version control
- **Metadata Export**: Export complete change data as JSON for programmatic access

## Installation

1. Clone the repository:
```bash
git clone https://github.com/shailashiv/gerrit2git-archive.git
cd gerrit2git-archive
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

Export merged changes from Gerrit:

```bash
python run.py --gerrit-url https://gerrit.example.com --query "status:merged" --repo-path ./gerrit-history
```

### Command Line Options

```bash
python run.py --help
```

**Required:**
- `--gerrit-url`: Gerrit server URL (e.g., `https://gerrit.example.com`)

**Optional:**
- `--username`: Gerrit username (for authenticated access)
- `--password`: Gerrit HTTP password (for authenticated access)
- `--query`: Gerrit query string (default: `status:merged`)
- `--limit`: Maximum number of changes to fetch (default: 1000)
- `--output-dir`: Directory for HTML and patch files (default: `./gerrit-export`)
- `--repo-path`: Path to git repository (default: `./gerrit-history-repo`)
- `--branch`: Git branch name (default: `gerrit-history`)
- `--export-only`: Export patches and HTML only, skip git repository creation
- `--no-verify-ssl`: Disable SSL certificate verification

### Examples

**Export all merged changes:**
```bash
python run.py --gerrit-url https://gerrit.example.com \
  --query "status:merged" \
  --repo-path ./gerrit-history
```

**Export specific project:**
```bash
python run.py --gerrit-url https://gerrit.example.com \
  --query "project:my-project AND status:merged" \
  --repo-path ./my-project-history
```

**Export with authentication:**
```bash
python run.py --gerrit-url https://gerrit.example.com \
  --username john.doe \
  --password your-http-password \
  --query "status:merged"
```

**Export without creating git repository:**
```bash
python run.py --gerrit-url https://gerrit.example.com \
  --export-only \
  --output-dir ./exports
```

## Output Structure

```
gerrit-history-repo/
├── README.md
├── patches/
│   ├── 12345-Add_new_feature.patch
│   ├── 12346-Fix_bug.patch
│   └── ...
└── html/
    ├── index.html
    ├── 12345-Add_new_feature.html
    ├── 12346-Fix_bug.html
    └── ...

gerrit-export/
├── patches/         # Copy of all patch files
├── html/            # Copy of all HTML files
└── metadata/        # JSON metadata export
    └── gerrit_export_metadata.json
```

## Testing

Run integration tests:
```bash
python tests/test_integration.py
```

Run demo with mock data:
```bash
python demo_simple.py
```

## Project Structure

```
gerrit2git-archive/
├── src/
│   ├── __init__.py
│   ├── main.py                 # Main entry point
│   ├── gerrit_api.py           # Gerrit REST API client
│   ├── git_manager.py          # Git repository operations
│   ├── html_generator.py       # HTML generation
│   ├── history_preserver.py    # Main orchestrator
│   └── metadata_exporter.py    # JSON metadata export
├── tests/
│   ├── __init__.py
│   ├── test_integration.py     # Integration tests
│   └── mock_gerrit_server.py   # Mock Gerrit server for testing
├── run.py                      # Simple entry point
├── demo_simple.py              # Demo script
├── requirements.txt
├── pyproject.toml
└── README.md
```

## How It Works

1. **Fetch Changes**: Connects to Gerrit REST API and fetches changes based on your query
2. **Export Patches**: Downloads patch files for each change
3. **Generate HTML**: Creates individual HTML pages for each change with full review data
4. **Create Index**: Generates a searchable HTML index of all changes
5. **Git Storage**: Copies all files to a git repository and commits them
6. **Export Metadata**: Saves complete change data as JSON

## Gerrit Query Syntax

Use standard Gerrit query syntax for the `--query` parameter:

- `status:merged` - All merged changes
- `status:open` - All open changes
- `project:my-project` - Changes in specific project
- `branch:main` - Changes on specific branch
- `owner:john.doe` - Changes by specific owner
- `after:2025-01-01` - Changes after specific date

Combine with `AND`, `OR`, `NOT`:
```bash
--query "project:my-project AND status:merged AND after:2025-01-01"
```

## Requirements

- Python 3.8+
- Git
- requests library
