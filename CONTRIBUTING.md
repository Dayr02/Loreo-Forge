# Contributing

## Branching

- `main` is production-only and protected.
- `develop` is the integration branch for active work.
- Use `feature/{phase-number}/{feature-name}` for implementation branches.
- Use `release/v{major}.{minor}` for stabilization.
- Use `hotfix/{issue}` for emergency fixes from `main`.

## Commit Format

Use `type(scope): summary`.

Allowed types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `style`

Common scopes: `phase-N`, `bridge`, `forge`, `godot`, `db`, `ai`, `ui`, `build`

## Pull Requests

- Open PRs against `develop` unless preparing a release.
- Make sure `pytest`, linting, and workflow validation pass.
- Reference the phase and acceptance criteria in the PR body.
- Avoid committing runtime data from `data/` or Godot cache files.

## Phase Completion Checklist

- CI is green.
- Schema migrations run cleanly on existing databases.
- Tests cover the new behavior.
- Architecture-impacting changes are documented.
