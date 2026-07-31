# Engineering Decisions

## Why the shared utilities import changed

The original job scripts appended a hardcoded
`/Workspace/Users/<employee-email>/team-repo/databricks/dbricks-utils` path to
`sys.path` and did `import common_utils as u`. That pattern ties every consumer to
one person's workspace directory and can't be pip-installed or version-pinned.

In this repository, `shared/logistics_data_utils` is a proper installable Python
package (see [../../../shared/logistics_data_utils](../../../shared/logistics_data_utils)).
The entry-point scripts here do `import logistics_data_utils as u` with no
`sys.path` manipulation. In a real Databricks bundle deployment, the package would
be installed as a job library (wheel or workspace library), not referenced by a
personal path — the commented-out `# - whl: ...` line in
[config/databricks.bundle.example.yml](../config/databricks.bundle.example.yml)
shows where that would go.

## Why the run identity is a variable, not a real default

`databricks.yml` originally hardcoded a specific employee's email as the job's
`on_failure` notification recipient and implicitly ran as that person, because a
dedicated service principal was not available on that workspace at the time. The
public template here makes `run_as_user` a required bundle variable with no shipped
default, and documents (in the bundle file's header comment) that a real
organizational deployment should use a service principal instead.

## Why the config format stayed JSON, not YAML

The target structure convention for this portfolio suggests `config/config.example.yml`,
but this project's actual runtime code loads a JSON config via
`u.load_config(base_dir=...)` (backed by `json.load`). Converting the shipped
example to YAML without also rewriting the loader would misrepresent what the code
actually does, so `config/config.example.json` was kept instead — this is a
deliberate, documented deviation from the general template, not an oversight.

## Why SQL files moved to a sibling `sql/` folder instead of staying in `src/`

The target project layout separates `src/` (code) from `sql/` (queries). Both
Python entry points now resolve query paths via
`Path(__file__).resolve().parent.parent / "sql"` instead of assuming the query file
sits next to the script.
