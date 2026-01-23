<!--
SYNC IMPACT REPORT
==================
Version change: N/A → 1.0.0 (initial ratification)
Modified principles: N/A (initial creation)
Added sections:
  - Core Principles (3 principles)
  - Development Workflow
  - Governance
Removed sections: N/A
Templates requiring updates:
  - .specify/templates/plan-template.md ✅ (already compatible - Constitution Check section)
  - .specify/templates/spec-template.md ✅ (already compatible - requirements-focused)
  - .specify/templates/tasks-template.md ✅ (already compatible - no testing enforcement)
  - .specify/templates/checklist-template.md ✅ (already compatible)
  - .specify/templates/agent-file-template.md ✅ (already compatible)
Follow-up TODOs: None
-->

# Basidian Constitution

## Core Principles

### I. Testable Design

All components, modules, and functions MUST be designed for testability. This means:

- Functions have clear inputs and outputs with minimal side effects
- Dependencies are injectable rather than hardcoded
- State is isolated and manageable
- Public interfaces are well-defined

Writing tests is OPTIONAL. The requirement is that code CAN be tested when needed, not that tests MUST exist. When tests are written, they should be meaningful and cover actual risk areas.

**Rationale**: Testable code is inherently better structured, easier to refactor, and more maintainable. Enforcing testability without mandating tests keeps velocity high while preserving quality options.

### II. Balanced Architecture

Frontend (Flutter) and backend (Python/FastAPI) evolve together as equal partners:

- Neither layer dictates to the other; both inform the design
- API contracts are defined collaboratively when features span both layers
- Changes to shared interfaces require consideration of both sides
- Each layer maintains its own idioms and best practices

**Rationale**: Basidian is a full-stack application where user experience and backend capabilities must align. Rigid API-first or UI-first approaches create friction; balanced evolution produces cohesive features.

### III. Pragmatic Simplicity

Start with the simplest solution that meets current requirements:

- Avoid adding features, abstractions, or configurations until explicitly needed
- Forward-thinking design is acceptable when the cost is low and the benefit is clear
- Complexity MUST be justified in code comments or commit messages when introduced
- Refactor toward simplicity when requirements stabilize

**Rationale**: Over-engineering wastes effort and creates maintenance burden. Pragmatic simplicity balances YAGNI discipline with practical recognition that some abstractions pay for themselves immediately.

## Development Workflow

### Code Quality

- Code review is encouraged for non-trivial changes
- Linting and formatting tools SHOULD be configured and used consistently
- Documentation is written when behavior is non-obvious; avoid redundant comments

### Feature Development

- Features SHOULD start with user scenarios (who, what, why)
- Implementation proceeds in small, reviewable increments
- Both frontend and backend changes for a feature SHOULD be coordinated

### Deployment

- Changes are tested locally before deployment
- Database migrations are reversible when feasible
- Breaking API changes require version bumps or deprecation periods

## Governance

This constitution establishes non-negotiable principles for Basidian development.

**Amendment Process**:
1. Propose changes via discussion with project maintainers
2. Document rationale for additions, modifications, or removals
3. Update version number according to semantic versioning:
   - MAJOR: Principle removed or fundamentally redefined
   - MINOR: New principle added or existing principle materially expanded
   - PATCH: Clarifications, wording improvements, non-semantic changes
4. Update LAST_AMENDED_DATE to the date of change

**Compliance**: All pull requests and code reviews SHOULD verify alignment with these principles. Violations require explicit justification.

**Version**: 1.0.0 | **Ratified**: 2026-01-09 | **Last Amended**: 2026-01-09
