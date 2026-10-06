---
title: "Contributing to gsa-compliance-robot"
status: canonical
---

# Contributing to gsa-compliance-robot

## Before You Start

This package is a dependency consumed by other GSA-TTS compliance/audit
repositories ([`M-26-14`](https://github.com/GSA-TTS/M-26-14),
[`gsa-pages`](https://github.com/GSA-TTS/gsa-pages)), once their migration
issues ([#11](https://github.com/GSA-TTS/robotframework-compliance-kit/issues/11),
[#12](https://github.com/GSA-TTS/robotframework-compliance-kit/issues/12))
land. Treat every keyword rename or signature change as a breaking change
for those consumers, even before migration lands — the point of this
package is to be a stable target for them to adopt.

Before opening a change:

1. Review the related issue or create one if none exists.
2. Keep the change scoped to one concern.
3. Do not include credentials, private keys, production data, or local
   `.env` content.
4. Do not report security vulnerabilities in public GitHub issues. Follow
   [SECURITY.md](./SECURITY.md).

## Development Setup

```bash
uv sync --extra dev
```

For Browser or Allure keyword development:

```bash
uv sync --extra dev --extra browser --extra allure
uv run rfbrowser init
```

## Verification

```bash
uv run pytest --cov=gsa_compliance_robot --cov-report=term-missing
uv run robocop check --config robocop.toml src/
```

Target \u226590% branch coverage for new Python modules — this package's secret
masking and auth code is security-critical for every downstream consumer.

## Breaking Changes

Any keyword rename or signature change requires:

1. A deprecation shim — the old keyword name logs a `WARN` and delegates to
   the new one for at least one minor release.
2. A `CHANGELOG.md` entry under "Changed" or "Deprecated".
3. Explicit callout in the PR description of which consumer repos
   (M-26-14, gsa-pages) need a follow-up PR.

## Pull Requests

Each PR should include:

- Summary of the change and why it is needed
- Related issue links
- Verification commands and results (pytest + robocop output)
- Which consumer repos are affected, if any
- AI attribution when AI assistance was used

## License

By contributing, you agree your contribution is released under CC0 1.0
(see [LICENSE](./LICENSE)) — public domain, no copyright claimed.
