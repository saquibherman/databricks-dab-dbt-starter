import os
import sys

import pytest

# dab_project is importable via `pythonpath = ["src"]` in pyproject.toml (no sys.path changes needed).


# Returning a Spark Session, shared by all tests in the run
@pytest.fixture(scope="session")
def spark():
    try:
        from databricks.connect import DatabricksSession
    except ImportError:
        DatabricksSession = None

    if DatabricksSession is not None:
        # .venv_dbc: run on Databricks serverless (DEFAULT profile has no cluster configured)
        yield DatabricksSession.builder.serverless().getOrCreate()
        return

    try:
        from pyspark.sql import SparkSession
    except ImportError:
        raise ImportError("Neither Databricks Session or Spark Session are available")

    # .venv_pyspark: local Spark. Workers must use this interpreter, not `python3` from PATH.
    os.environ["PYSPARK_PYTHON"] = sys.executable
    spark = SparkSession.builder.master("local[*]").getOrCreate()
    yield spark
    spark.stop()
