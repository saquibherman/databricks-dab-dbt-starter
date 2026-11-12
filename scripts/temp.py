import os

try:
    from databricks.connect import DatabricksSession

    builder = DatabricksSession.builder
    # Databricks Connect needs compute: use the cluster if one is set in the environment
    # (DATABRICKS_CLUSTER_ID or SPARK_REMOTE, e.g. from the VS Code extension), otherwise serverless.
    if not os.environ.get("DATABRICKS_CLUSTER_ID") and not os.environ.get("SPARK_REMOTE"):
        builder = builder.serverless()
    spark = builder.getOrCreate()
    print("Using DatabricksSession.")
except ImportError:
    try:
        from pyspark.sql import SparkSession

        spark = SparkSession.builder.getOrCreate()
        print("Using SparkSession.")
    except ImportError:
        raise ImportError("Neither DatabricksSession nor SparkSession could be imported.")
