# Plan: Logging Observability

**Spec**: specs/002-add-logging-observability/spec.md

## Tech Stack

- Backend: Python + loguru (file sink)
- Frontend: TypeScript + Tauri fs plugin (direct file writes)
- Log format: JSON Lines (one JSON object per line)

## Structure

```
$TEMP/basidian/                          # Platform temp directory
├── backend.log                          # Backend logs
└── frontend.log                         # Frontend logs

backend/src/basidian_server/
└── main.py                              # Add file logger

frontend/src-tauri/
├── Cargo.toml                           # Add tauri-plugin-fs
├── src/lib.rs                           # Register fs plugin
└── capabilities/default.json            # Add fs permissions

frontend/src/lib/utils/
└── logger.ts                            # Add Tauri fs sink
```

## Log Directory

Both frontend and backend write to the same temp directory:

| Platform | Path |
|----------|------|
| Linux | `/tmp/basidian/` |
| macOS | `$TMPDIR/basidian/` |
| Windows | `%TEMP%\basidian\` |
| Android | Tauri's `BaseDirectory.Temp` + `basidian/` |

## Log Format

JSON Lines. Each line is a valid JSON object:

```json
{"ts":"2024-01-22T10:30:45.123Z","level":"info","module":"DailyNotes","msg":"Opening today's note","data":{"date":"2024-01-22"}}
```

Fields:
- `ts` - ISO 8601 timestamp
- `level` - debug/info/warn/error
- `module` - Source module name
- `msg` - Log message
- `data` - Optional structured data (omitted if empty)

## Approach

### 1. Backend file logging

Add loguru file sink with JSON format to temp directory:

```python
import json
import tempfile
from pathlib import Path

LOG_DIR = Path(tempfile.gettempdir()) / "basidian"
LOG_DIR.mkdir(exist_ok=True)

def file_sink(message):
    record = message.record
    entry = {
        "ts": record["time"].isoformat(),
        "level": record["level"].name.lower(),
        "module": record["name"],
        "msg": record["message"],
    }
    with open(LOG_DIR / "backend.log", "a") as f:
        f.write(json.dumps(entry) + "\n")

logger.add(file_sink, level="DEBUG")
```

Log the path on startup so users know where to find logs.

### 2. Add Tauri fs plugin

**Cargo.toml** - add dependency:
```toml
[dependencies]
tauri-plugin-fs = "2"
```

**lib.rs** - register plugin:
```rust
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_fs::init())
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

**capabilities/default.json** - create with fs permissions:
```json
{
  "$schema": "https://schemas.tauri.app/config/2/capabilities",
  "identifier": "default",
  "windows": ["main"],
  "permissions": [
    "core:default",
    "fs:default",
    "fs:allow-write-text-file",
    "fs:allow-create",
    "fs:allow-exists",
    "fs:allow-mkdir"
  ]
}
```

### 3. Update frontend logger

Add Tauri fs writes to temp directory:

```typescript
import { writeTextFile, mkdir, exists, BaseDirectory } from '@tauri-apps/plugin-fs';

class Logger {
    private logQueue: string[] = [];
    private flushTimeout: ReturnType<typeof setTimeout> | null = null;
    private isTauri = '__TAURI__' in window;

    private async ensureLogDir() {
        if (!this.isTauri) return;
        const dirExists = await exists('basidian', { baseDir: BaseDirectory.Temp });
        if (!dirExists) {
            await mkdir('basidian', { baseDir: BaseDirectory.Temp, recursive: true });
        }
    }

    private async flushToFile() {
        if (this.logQueue.length === 0 || !this.isTauri) return;

        const lines = this.logQueue.join('');
        this.logQueue = [];

        await this.ensureLogDir();
        await writeTextFile('basidian/frontend.log', lines, {
            baseDir: BaseDirectory.Temp,
            append: true
        });
    }

    private queueLogEntry(entry: object) {
        this.logQueue.push(JSON.stringify(entry) + '\n');

        // Batch writes - flush every 100ms
        if (!this.flushTimeout) {
            this.flushTimeout = setTimeout(() => {
                this.flushTimeout = null;
                this.flushToFile().catch(() => {});
            }, 100);
        }
    }

    private log(level: LogLevel, module: string, message: string, data?: unknown) {
        // Existing console logging...

        // Queue for file
        this.queueLogEntry({
            ts: new Date().toISOString(),
            level,
            module,
            msg: message,
            ...(data !== undefined && { data })
        });
    }
}
```

### 4. Install frontend npm package

```bash
cd frontend && npm install @tauri-apps/plugin-fs
```

## Risks

- **Tauri fs plugin not available in browser dev mode**: Check `'__TAURI__' in window` before using fs API. Falls back to console-only.
- **Temp directory cleared on reboot**: Acceptable for debugging logs. Not meant for permanent storage.

## Open Questions

None.
