# dab_dbt_project

Databricks Declarative Automation Bundle (DAB) template with CI/CD, PySpark and **dbt**.
The Citi Bike medallion pipeline runs as one Databricks job:

| Layer  | Built by                                   | Output                         |
|--------|--------------------------------------------|--------------------------------|
| Bronze | PySpark notebook `01_bronze_citibike`      | `<catalog>.01_bronze.jc_citibike` |
| Silver | PySpark notebook `02_silver_citibike` (+ `dab_project` wheel) | `<catalog>.02_silver.jc_citibike` |
| Gold   | **dbt** task `03_gold_dbt` (`dbt build`)   | `<catalog>.03_gold.daily_ride_summary`, `daily_station_performance` |

`<catalog>` is `citibike_dev` / `citibike_test` / `citibike_prod` per bundle target.

* `src/`: Python package `dab_project` (shared PySpark code, built as a wheel).
* `citibike_etl/`: bronze/silver notebooks and a Lakeflow declarative pipeline variant.
* `dbt/`: dbt project for the gold layer (see [dbt](#dbt-gold-layer)).
* `resources/`: job, pipeline and cluster definitions.
* `tests/`: PySpark unit tests (pytest).
* `.github/workflows/`: CI (pytest + dbt checks on pull requests) and CD (deploy test, then prod).


## Getting started

Choose how you want to work on this project:

(a) Directly in your Databricks workspace, see
    https://docs.databricks.com/dev-tools/bundles/workspace.

(b) Locally with an IDE like Cursor or VS Code, see
    https://docs.databricks.com/dev-tools/vscode-ext.html.

(c) With command line tools, see https://docs.databricks.com/dev-tools/cli/databricks-cli.html

If you're developing with an IDE, dependencies for this project should be installed using uv:

*  Make sure you have the UV package manager installed.
   It's an alternative to tools like pip: https://docs.astral.sh/uv/getting-started/installation/.
*  Run `uv sync --dev` to install the project's dependencies.


## Local Python environments

Two local virtual environments are used, both on Python 3.12 and pinned to
Databricks Runtime 18 LTS (Apache Spark 4.1.0). Both folders are git-ignored; recreate them
with the commands below.

| Environment     | Use it for                                                                 | Defined by                                       |
|-----------------|----------------------------------------------------------------------------|--------------------------------------------------|
| `.venv_dbc`     | Running code against Databricks compute (Databricks Connect), tests, notebooks | `pyproject.toml` + `uv.lock`                     |
| `.venv_pyspark` | Fully local, offline open-source PySpark (no workspace needed)             | `requirements-pyspark.txt`                       |

> Don't install `pyspark` into `.venv_dbc`: it conflicts with `databricks-connect`.

### `.venv_dbc` (Databricks Connect)

```bash
# Recommended: let the Databricks CLI build it, matched to your compute
databricks environments setup-local --profile <PROFILE>

# Or with plain uv from the lock file
UV_PROJECT_ENVIRONMENT=.venv_dbc uv sync --dev
```

The `[tool.uv]` constraints in `pyproject.toml` are managed by `databricks environments setup-local`;
don't edit them by hand. Add runtime dependencies with `uv add <package>` and dev tools with
`uv add --dev <package>`.

Databricks Connect needs compute: pass `.serverless()` or a cluster ID to `DatabricksSession.builder`,
or set `serverless_compute_id = auto` (or `cluster_id = ...`) in your `~/.databrickscfg` profile.

### `.venv_pyspark` (local PySpark)

```bash
uv venv .venv_pyspark --python 3.12
uv pip install --no-config --python .venv_pyspark/bin/python -r requirements-pyspark.txt
uv pip install --no-config --python .venv_pyspark/bin/python --no-deps -e .   # optional: import dab_project
```

`--no-config` is required so uv ignores the Databricks Connect constraints in `pyproject.toml`.
Requires Java 17+ (`JAVA_HOME`). Startup warnings (incubator modules, loopback address,
native-hadoop) are harmless.

### Using them in VS Code

Select the interpreter or notebook kernel with **Python: Select Interpreter** /
**Select Kernel → Python Environments** and pick `.venv_dbc/bin/python` or
`.venv_pyspark/bin/python`.

### Running tests

Unit tests live in `tests/` and take a shared `spark` fixture from `tests/conftest.py`.
Where they run depends on the environment:

| Environment     | Spark used                                           | Needs                                  |
|-----------------|------------------------------------------------------|----------------------------------------|
| `.venv_pyspark` | Local open-source Spark (`local[*]`)                 | Java 17+; no workspace, no credentials |
| `.venv_dbc`     | Databricks serverless via Databricks Connect         | `DEFAULT` profile in `~/.databrickscfg` |

```bash
# Local Spark (recommended day to day; also what CI uses)
.venv_pyspark/bin/python -m pytest
uv run --no-project --python .venv_pyspark/bin/python pytest   # same, via uv

# Databricks serverless
.venv_dbc/bin/python -m pytest
UV_PROJECT_ENVIRONMENT=.venv_dbc uv run pytest                  # same, via uv
```

Or activate an environment (`source .venv_pyspark/bin/activate`) and run `pytest`.

- `--no-project` is required for `.venv_pyspark`: otherwise `uv run` syncs the project into it and
  installs `databricks-connect`, which conflicts with `pyspark`.
- `uv run` syncs `.venv_dbc` to `uv.lock` first, removing packages installed by hand; add packages
  with `uv add` / `uv add --dev` instead.
- Plain `uv run pytest` uses (and creates if needed) a separate `.venv` with Databricks Connect.
- `dab_project` is imported from `src/` via `pythonpath = ["src"]` in `pyproject.toml`; no install needed.

Writing a test: add `spark` as a parameter to get the right session automatically.

```python
def test_something(spark):
    df = spark.createDataFrame([(1,)], "x int")
    assert df.count() == 1
```

Useful options: `pytest -q`, `pytest -x` (stop at first failure), `pytest -k duration`
(select by name), `pytest tests/test_citibike_utils.py` (one file).

## dbt (gold layer)

The dbt project in `dbt/` builds the gold tables from the silver table and replaces the former
gold notebooks.

```
dbt/
├── dbt_project.yml          # gold models -> schema 03_gold, materialized as Delta tables
├── dbt_profiles/profiles.yml # targets dev / test / prod (catalog + SQL warehouse per workspace)
├── packages.yml             # dbt_utils
├── macros/                  # generate_schema_name (use 03_gold as-is), round_minutes
├── models/sources/          # silver.jc_citibike source + docs + source tests
├── models/gold/             # gold models, model contracts, data tests, unit tests
└── tests/generic/           # assert_non_negative generic test
```

**What `dbt build` runs:** unit tests (logic on mocked rows), the two gold models (with enforced
contract on `daily_ride_summary`), and data tests (`not_null`, `unique`, `assert_non_negative`,
`dbt_utils.unique_combination_of_columns`).

### On Databricks

The job task `03_gold_dbt` runs `dbt deps` and `dbt build --target=${bundle.target}` on serverless
compute (`dbt_env` environment) against the target's SQL warehouse. Databricks sets `DBT_HOST` and
`DBT_ACCESS_TOKEN` for the job's `run_as` identity, so no secrets are stored. In test/prod that
identity is the service principal, which needs **CAN USE** on the SQL warehouse and Unity Catalog
grants on the catalog (read `02_silver`, create/modify in `03_gold`).

### Running dbt locally

```bash
# one-time: create .venv_dbt
uv venv .venv_dbt --python 3.12
uv pip install --no-config --python .venv_dbt/bin/python -r requirements-dbt.txt

# connection for the dev workspace (host without https://, a token, and the SQL warehouse ID)
export DBT_HOST=<dev-workspace-host>           # e.g. adb-1234567890123456.7.azuredatabricks.net
export DBT_WAREHOUSE_ID=<sql-warehouse-id>      # SQL Warehouses > your warehouse > Connection details
export DBT_ACCESS_TOKEN=<personal-access-token>

cd dbt
../.venv_dbt/bin/dbt deps  --profiles-dir dbt_profiles
../.venv_dbt/bin/dbt debug --profiles-dir dbt_profiles            # check the connection
../.venv_dbt/bin/dbt build --profiles-dir dbt_profiles --target dev
../.venv_dbt/bin/dbt test  --profiles-dir dbt_profiles --select test_type:unit   # unit tests only
../.venv_dbt/bin/dbt docs generate --profiles-dir dbt_profiles && ../.venv_dbt/bin/dbt docs serve --profiles-dir dbt_profiles
```

Format SQL with sqlfmt (CI checks it): `.venv_dbt/bin/sqlfmt dbt`

Keep `dbt-databricks` / `dbt-core` versions in `requirements-dbt.txt` and the `dbt_env` environment
in `resources/citibike_etl_pipeline_nb.job.yml` in sync.

## Building the wheel

```bash
uv build --wheel          # writes dist/dab_project-<version>-py3-none-any.whl
```

`databricks bundle deploy` builds and uploads the wheel automatically (see `artifacts` in
`databricks.yml`).


# Using this project using the CLI

The Databricks workspace and IDE extensions provide a graphical interface for working
with this project. It's also possible to interact with it directly using the CLI:

1. Authenticate to your Databricks workspace, if you have not done so already:
    ```
    $ databricks configure
    ```

2. To deploy a development copy of this project, type:
    ```
    $ databricks bundle deploy --target dev
    ```
    (Note that "dev" is the default target, so the `--target` parameter
    is optional here.)

    This deploys everything that's defined for this project.

3. Similarly, to deploy a production copy, type:
   ```
   $ databricks bundle deploy --target prod
   ```

4. To run a job or pipeline, use the "run" command:
   ```
   $ databricks bundle run
   ```

5. Finally, to run tests locally, use `pytest` (see [Running tests](#running-tests)):
   ```
   $ .venv_pyspark/bin/python -m pytest          # local Spark
   $ UV_PROJECT_ENVIRONMENT=.venv_dbc uv run pytest   # Databricks serverless
   ```
