# Contributing to Mapanare

Thanks for your interest in Mapanare.

Mapanare is still early, which means contributors can influence both the
implementation and the shape of the project. Code is important, but so are
good bug reports, docs, examples, benchmarks, and thoughtful design
feedback.

Before contributing, please read:

- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
- [GOVERNANCE.md](GOVERNANCE.md)
- [SECURITY.md](SECURITY.md) for private vulnerability reporting

## Setup

```bash
git clone https://github.com/Mapanare-Research/mapanare.git
cd mapanare
make install   # installs mapanare + dev dependencies
make test      # run the test suite
make lint      # black + ruff + mypy
```

Requires Python 3.11+.

## Ways to Contribute

You do not need to start with compiler internals.

- Fix bugs or add tests for existing behavior
- Improve documentation, tutorials, examples, or error messages
- Reproduce issues and reduce them to minimal failing cases
- Review RFCs and language proposals
- Help triage issues and answer questions in Discord
- Benchmark behavior and compare regressions across versions

## Development Workflow

1. Check whether an issue already exists, or open one for non-trivial work.
2. Create a branch from `main`.
3. Write the change and add or update tests.
4. Run `make lint` and `make test` before pushing.
5. Open a focused PR using the PR template. CI must pass.

If you are planning a larger change, especially in the compiler or language
design, start the discussion before writing a large patch.

## Code Style

Enforced automatically:

- **black** — formatter (line length 100)
- **ruff** — linter
- **mypy** — strict type checking

Run `make fmt` to auto-format. Pre-commit hooks are available via `.pre-commit-config.yaml`.

## Communication Channels

- GitHub issues: bug reports, scoped feature work, and task tracking
- Pull requests: implementation and code review
- [`docs/rfcs/`](docs/rfcs/): language design proposals and accepted design records
- Discord `#help`: usage questions and debugging help
- Discord `#compiler-dev`: contributor coordination for implementation work
- Security issues: follow [SECURITY.md](SECURITY.md), not public issues

## What to Work On

- Check open issues tagged with the current phase.
- Check the roadmap in [docs/PLAN-v0.4.0.md](docs/PLAN-v0.4.0.md).
- Join `#compiler-dev` on [Discord](https://discord.gg/5hpGBm3WXf) before building major features.
- Read [docs/SPEC.md](docs/SPEC.md) to understand the language design.
- Read [docs/ROADMAP.md](docs/ROADMAP.md) for the broader project direction.

## Language Changes

Any non-trivial change to Mapanare's syntax, semantics, or user-visible
language behavior requires an RFC in [`docs/rfcs/`](docs/rfcs/).

Open or link a discussion first if the shape of the change is still unclear.
Accepted RFCs are the source of truth for major language design decisions.
See [GOVERNANCE.md](GOVERNANCE.md) for the full decision model.

## Maintainer Path

Mapanare is currently led under a BDFL model by Juan Denis, but the project
is intended to grow beyond a single maintainer.

Contributors who consistently do high-quality work, participate in review,
and show good judgment may be invited into expanded responsibilities over
time. See [GOVERNANCE.md](GOVERNANCE.md) for the maintainer path and
decision-making process.

## PR Guidelines

- Keep PRs focused. One feature or fix per PR.
- Include tests that cover the change.
- Update `CHANGELOG.md`, docs, or examples if the change is user-facing.
- Link the relevant issue. If the change affects language design, link the RFC.
- CI checks (black, ruff, mypy, pytest) must all pass.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
