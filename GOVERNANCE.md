# Governance

Mapanare is an early-stage open source programming language project. At this
stage the project uses a Benevolent Dictator For Life (BDFL) model so the
language, compiler, and community can evolve with a clear final decision
maker while the project is still small.

## Project Lead

Juan Denis is the project lead and current BDFL for Mapanare.

The project lead has final responsibility for:

- Language syntax and semantics
- Roadmap and release direction
- Accepting or rejecting RFCs
- Appointing and removing maintainers
- Resolving deadlocked technical or community decisions

The project lead is expected to explain major decisions in public whenever
practical so contributors can understand the reasoning behind them.

## Maintainers

Maintainers are trusted contributors with merge and triage authority.

Maintainers are expected to:

- Review pull requests and help contributors get changes landed
- Triage issues, label work, and keep discussions actionable
- Enforce the Code of Conduct in community spaces
- Protect project quality, release discipline, and documentation accuracy
- Escalate major product, governance, or security decisions when needed

Maintainers may merge routine fixes in their area of responsibility, but
they should avoid merging their own non-trivial pull requests without an
independent review.

## Contributors

Contributors include anyone who improves Mapanare through code, tests,
documentation, benchmarks, issue triage, design discussion, or community
support. Contribution is not limited to compiler code.

## Decision Making

Mapanare uses the lightest process that preserves clarity:

- Routine fixes and documentation updates are handled through normal PR
  review and maintainer judgment.
- Changes that affect language design, roadmap priorities, or community
  policy should happen in public on GitHub first.
- When maintainers disagree and consensus does not emerge, the project lead
  makes the final call.

Consensus is preferred, but ambiguity is worse than a clear decision.

## RFC Process

RFCs are the mechanism for non-trivial, user-visible design changes.

An RFC is required for:

- New syntax, keywords, or language constructs
- Changes to language semantics or type-system behavior
- Breaking changes to the standard library or package tooling
- Major module, concurrency, memory, runtime, or FFI design changes
- Deprecations or removals that affect existing user code

An RFC is usually not required for:

- Bug fixes that align implementation with the existing spec
- Internal refactors with no user-visible behavior change
- Tests, docs, examples, and benchmark updates
- Small quality-of-life improvements that do not change semantics

### RFC Workflow

1. Start with an issue or a focused discussion so the problem is clear.
2. Draft the proposal in `docs/rfcs/` using the next available four-digit
   number and a short descriptive filename.
3. Include motivation, detailed design, alternatives considered,
   compatibility notes, and open questions.
4. Leave enough time for review. As a rule, non-trivial RFCs should stay
   open for at least 7 days before a final decision.
5. The project lead accepts, requests revisions to, or rejects the RFC.

Code may be prototyped before an RFC is accepted, but landing a major design
change requires explicit approval.

## Maintainer Path

Mapanare intends to grow beyond a one-person project. Maintainer access is
earned through sustained, high-trust contribution rather than requested on
day one.

Signals that someone may be ready for expanded responsibility include:

- At least 5 high-quality merged pull requests
- Consistent review participation and constructive technical judgment
- Reliable follow-through on bugs, docs, or contributor support
- Respectful collaboration aligned with the Code of Conduct
- Understanding of the language vision and release quality bar

The typical path is:

1. Contributor builds a visible record of useful work
2. A maintainer or the project lead proposes expanded responsibility
3. The contributor may receive a limited trial period with triage or merge
   access
4. The project lead confirms maintainer status

Maintainer access may be paused or removed for inactivity, repeated poor
judgment, Code of Conduct violations, or loss of trust.

## Bus Factor and Succession

The project currently has a bus factor of 1 for final authority. That risk is
acknowledged explicitly.

The near-term goal is to expand the maintainer group before `1.0`.

If the project lead becomes temporarily unavailable:

- Maintainers may continue routine triage, docs work, test fixes, and
  low-risk bug fixes
- Maintainers should avoid irreversible governance or language changes until
  the project lead returns

If the project lead is absent for an extended period with no communicated
plan, maintainers may open a public governance issue proposing an interim
stewardship plan.

## Official Channels

The project's official public channels are:

- GitHub issues and pull requests for the canonical record
- `docs/rfcs/` for language design proposals
- Discord for onboarding, help, community discussion, and contributor
  coordination

Security issues must follow [SECURITY.md](SECURITY.md), not public issue
threads.

## Changes to Governance

This document can evolve as the project grows. Until a broader governance
body exists, governance changes are proposed publicly and approved by the
project lead.
