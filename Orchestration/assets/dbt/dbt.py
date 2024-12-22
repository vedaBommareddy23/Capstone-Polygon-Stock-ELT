import os
from pathlib import Path
from dagster import AssetExecutionContext, Config
from dagster_dbt import DbtCliResource, dbt_assets
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Configure dbt project directory
dbt_project_dir = Path(__file__).joinpath("..", "..", "..", "..", "Transformation", "polygon_dbt").resolve()
logger.info(f"DBT Project Directory: {dbt_project_dir}")

# Ensure project directory exists
if not dbt_project_dir.exists():
    raise ValueError(f"DBT project directory does not exist: {dbt_project_dir}")

# Configure dbt CLI resource
dbt_warehouse_resource = DbtCliResource(
    project_dir=str(dbt_project_dir=os.fspath(dbt_project_dir)),
    profiles_dir=str(dbt_project_dir)
)

# Define manifest path
dbt_manifest_path = 'Transformation/polygon_dbt/target/manifest.json'
logger.info(f"DBT Manifest Path: {dbt_manifest_path}")

dbt_manifest_path_1 = (
        dbt_warehouse_resource.cli(
            ["--quiet", "parse", "--target", "prod"],
            target_path=Path("target"),
        )
        .wait()
        .target_path.joinpath("manifest.json")
)
logger.info(f"DBT Manifest Path*****: {dbt_manifest_path_1}")

@dbt_assets(manifest=str(dbt_manifest_path))
def dbt_warehouse(context: AssetExecutionContext, dbt_warehouse_resource: DbtCliResource):
    """DBT warehouse assets."""
    # Log current working directory and environment
    logger.info(f"Current working directory: {os.getcwd()}")
    logger.info(f"DBT project directory exists: {os.path.exists(str(dbt_project_dir))}")
    
    try:
        # Run dbt parse first
        context.log.info("Running dbt parse...")
        dbt_warehouse_resource.cli(["parse"], context=context).wait()
        
        # Then run dbt build
        context.log.info("Running dbt build...")
        yield from dbt_warehouse_resource.cli(["build"], context=context).stream()
    except Exception as e:
        context.log.error(f"Error running dbt: {str(e)}")
        raise