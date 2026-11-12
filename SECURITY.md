# Security Policy

## Supported versions

Only the latest release of the `v1` major version is supported. Using `@v1` always gives
you the latest fixes.

## Reporting a vulnerability

Please **do not open a public issue** for security problems.

Report privately via GitHub:
[Security → Report a vulnerability](https://github.com/spidero/github-stats-card/security/advisories/new).
You should get a response within a few days. Once fixed, a new release is published and the
advisory is disclosed.

## Notes for users

- The action only **reads** data through the GitHub GraphQL API. The token you pass
  (`GITHUB_TOKEN` or a personal access token) is used only for that request and never written
  to the generated files or logs.
- For private-repository stats use a **fine-grained, read-only** personal access token
  (Metadata, Pull requests, Issues: read) and store it as a repository secret.
- Generated SVGs contain only aggregated numbers and language names, never private
  repository names.
