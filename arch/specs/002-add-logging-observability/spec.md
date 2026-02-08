# Spec: Logging Observability

## Problem

When something doesn't work (like the "today note" button), there's no easy way to see what happened. Logs go to browser console and terminal stderr - not accessible from files.

## Requirements

1. All frontend logs write to a log file
2. All backend logs write to a log file
3. Log format is easy for AI agents to parse
4. Works on Windows, macOS, and Linux
5. Logs include enough context to debug issues (timestamp, module, level, message, data)

## Out of Scope

- Log rotation
- Remote log shipping
- Log aggregation services
