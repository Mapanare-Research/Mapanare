# Contributing to Mapanare

Thanks for your interest in Mapanare. This guide covers everything you need to get started.

## Setup

```bash
git clone https://github.com/Mapanare-Research/mapanare.git
cd mapanare
make install   # installs mapanare + dev dependencies
make test      # run the test suite
make lint      # black + ruff + mypy
```

Requires Python 3.11+.

## Development Workflow

1. Create a branch from `main`.
2. Write your code. Write tests for your code.
3. Run `make lint` and `make test` before pushing.
4. Open a PR. CI must pass. All PRs require tests.

## Code Style

Enforced automatically:

- **black** — formatter (line length 100)
- **ruff** — linter
- **mypy** — strict type checking

Run `make fmt` to auto-format. Pre-commit hooks are available via `.pre-commit-config.yaml`.

## What to Work On

- Check open issues tagged with the current phase.
- Join `#compiler-dev` on [Discord](https://discord.gg/mapanare) before building major features.
- Read [SPEC.md](SPEC.md) to understand the language design.
- Read [ROADMAP.md](ROADMAP.md) for the project plan.

## Language Changes

Any change to Mapanare's syntax or semantics requires an RFC in the [rfcs](https://github.com/Mapanare-Research/rfcs) repo. Open an RFC before writing compiler code for new language features.

## PR Guidelines

- Keep PRs focused. One feature or fix per PR.
- Include tests that cover the change.
- Update CHANGELOG.md if the change is user-facing.
- CI checks (black, ruff, mypy, pytest) must all pass.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
