# Basync CLI

Push and pull files between Basidian's virtual filesystem and a local directory.

## What Users Can Do

1. **Push local files to Basidian**
   User uploads files from a local directory into Basidian's vault.
   - Works when: Local files are readable, creates/updates matching entries in Basidian
   - Fails when: Local path doesn't exist, shows clear error message

2. **Pull files from Basidian to local**
   User exports Basidian vault contents to a local directory.
   - Works when: Basidian has files, creates local files matching the virtual structure
   - Fails when: Local directory not writable, shows permission error

3. **Preview changes before applying**
   User sees what would happen without making changes.
   - Works when: Shows list of files to add, update, or delete
   - Fails when: Never fails, always shows preview

## Requirements

### Core
- [ ] Connect to Basidian backend via HTTP API
- [ ] Map local directory to Basidian path (e.g., `./notes` ↔ `/`)
- [ ] Support push and pull commands
- [ ] Preserve folder structure on both sides

### Filtering
- [ ] Support include/exclude file patterns (e.g., `--include "*.md"`)
- [ ] Skip hidden files and common ignores (.git, .DS_Store, node_modules)
- [ ] Target specific Basidian paths (e.g., `basync pull /projects`)

### User Experience
- [ ] Dry-run mode shows changes without applying them
- [ ] Show progress during operations (file count, current file)
- [ ] Exit with non-zero code on errors
- [ ] Config file for default settings (backend URL, local path, ignores)

## Open Questions

None - ready for planning.
