# Plan: Basync CLI

**Spec**: specs/002-basync-cli/spec.md

## Tech Stack

- Language: Python 3.12+
- CLI Framework: Click (same as bscli)
- HTTP Client: httpx (async)
- File Matching: fnmatch (stdlib)
- Testing: pytest

## Structure

New CLI tool alongside bscli:

```
backend/src/basidian_server/
├── basync.py           # Main CLI and commands
├── basync_client.py    # HTTP client for Basidian API
└── basync_config.py    # Config file loading
```

## Approach

### Core

1. **Connect to Basidian backend via HTTP API**
   Use httpx async client to call `/api/fs/` endpoints.
   - GET /api/fs/tree - list all nodes
   - POST /api/fs/node - create file/folder
   - PUT /api/fs/node/{id} - update file
   - DELETE /api/fs/node/{id} - delete file/folder

2. **Map local directory to Basidian path**
   - Local: `./notes/projects/readme.md`
   - Remote: `/projects/readme.md` (strip local prefix)
   - Config option: `--local ./notes --remote /`

3. **Support push and pull commands**
   - `basync push` - scan local dir, upload to API
   - `basync pull` - fetch from API, write to local

4. **Preserve folder structure on both sides**
   - Push: create folders before files
   - Pull: create directories with os.makedirs()

### Filtering

5. **Support include/exclude file patterns**
   - `--include "*.md"` - only match these
   - `--exclude "*.tmp"` - skip these
   - Use fnmatch for glob patterns

6. **Skip hidden files and common ignores**
   Default ignores: `.git`, `.DS_Store`, `node_modules`, `__pycache__`, `.env`
   Skip files starting with `.` unless explicitly included.

7. **Target specific Basidian paths**
   - `basync pull /projects` - only pull that subtree
   - `basync push /notes` - only push to that path

### User Experience

8. **Dry-run mode**
   - `--dry-run` flag on push/pull
   - Print what would happen, don't make changes
   - Format: `[+] create /path`, `[~] update /path`, `[-] delete /path`

9. **Show progress**
   - Print current file being processed
   - Show counts: `Processed 5/12 files`

10. **Exit codes**
    - 0: success
    - 1: error (API unreachable, permission denied, etc.)

11. **Config file**
    Location: `.basync.toml` in current directory
    ```toml
    backend_url = "http://localhost:8090"
    local_path = "./notes"
    remote_path = "/"
    exclude = [".git", "node_modules"]
    ```

## CLI Interface

```
basync push [OPTIONS] [PATH]
  --local PATH      Local directory (default: ./notes or config)
  --remote PATH     Remote Basidian path (default: / or config)
  --include PATTERN Only include matching files (repeatable)
  --exclude PATTERN Exclude matching files (repeatable)
  --dry-run         Show what would happen
  --url URL         Backend URL (default: http://localhost:8090)

basync pull [OPTIONS] [PATH]
  (same options as push)

basync config
  Show current config
```

## Risks

- **Large files**: Content stored as text in DB. For now, warn if file > 1MB.
- **Binary files**: Skip non-text files (check with file encoding).
- **API changes**: Pin to known API contract, version later if needed.

## Open Questions

None - ready for implementation.
