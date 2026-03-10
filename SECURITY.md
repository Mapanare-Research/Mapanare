# Security Policy

## Supported Versions

Mapanare is an early-stage language project. Security fixes are only
guaranteed for the actively developed code lines below.

| Version | Supported |
|---------|-----------|
| `main` | Yes |
| Latest tagged release | Yes |
| Older releases | No |

If you are running an older version, upgrade to the latest release or test
against the current `main` branch before reporting.

## Reporting a Vulnerability

Do not report security vulnerabilities through public GitHub issues,
Discord, or social media.

Use one of these private channels instead:

1. Preferred: GitHub Private Vulnerability Reporting for this repository,
   if it is enabled.
2. Fallback: email <juan@vene.co> with the subject
   `[Mapanare security]`.

Please include:

- A clear description of the issue and the affected component
- The version, commit SHA, or branch you tested
- Reproduction steps or a proof of concept
- The expected impact and any known prerequisites
- Whether the issue is already public anywhere else

If the report includes exploit code, keep it minimal and safe. Do not access
other people's systems, data, or accounts.

## Response Expectations

The project will make a good-faith effort to follow this timeline:

- Acknowledge receipt within 3 business days
- Provide an initial triage decision within 7 calendar days
- Share status updates at least weekly while the issue is being handled

Severe issues may require an out-of-band fix or a coordinated release. If a
report turns out not to be a vulnerability, the maintainer will still try to
explain the reasoning clearly.

## Disclosure Policy

Mapanare follows coordinated disclosure.

- Please allow time for investigation, mitigation, and a release before
  public disclosure.
- The project will normally aim to publish a fix or mitigation before full
  technical details are released.
- Reporters will be credited in release notes unless they prefer to remain
  anonymous.

## Scope

This policy covers vulnerabilities in the Mapanare compiler, CLI, runtime,
standard library, package tooling, install scripts, repository automation,
and documentation site code contained in this repository.

Security hardening work that does not represent a concrete vulnerability can
still be filed as a normal issue or PR when disclosure risk is low.
