# Security

This repository is a **sanitized portfolio of case studies**, not a deployable
system. See [docs/portfolio-scope.md](docs/portfolio-scope.md) for what that means
in practice.

## What is and isn't here

- No credentials, API keys, connection strings, or secrets are present anywhere in
  this repository, including in git history for this repository's own commits
  going forward from the reorganisation. See
  [docs/sanitization-report.md](docs/sanitization-report.md) for the sweep that
  confirmed this.
- Config files ship as `.example`/`.template` files with placeholder values only
  (e.g. `<TARGET_GOOGLE_SHEET_ID>`, `<SECRET_SCOPE>`, `<WORKSPACE_HOST>`). None of
  the placeholders are real defaults — every deployment target requires the
  operator to supply their own values.
- Bundle/deployment templates (`config/databricks.bundle.example.yml` in each
  featured project) do not contain a real workspace host, secret scope, cluster
  policy ID, or run-as identity.

## Reporting a concern

If you find a value in this repository that looks like a real credential,
hostname, internal identifier, or personal data that survived sanitization, please
open an issue describing the file and line — that would be a sanitization bug, and
this repository's author treats it as a priority fix. Do not open a public issue
containing the sensitive value itself; describe its location instead.

## Not a deployable copy

Every pipeline in this repository was extracted from a real internal system and
then rewritten to remove employer-identifying details, live credentials, and
production infrastructure references. Running the code here against real
infrastructure requires supplying your own workspace, secrets, and connection
details — none of which are provided or implied by any placeholder in this repo.
