from dagster import (
    Definitions,
    EnvVar,
    ScheduleDefinition,
    define_asset_job,
    load_assets_from_package_module,
    FilesystemIOManager,
)

# pip install dagster_duckdb_pandas
from dagster_duckdb_pandas import DuckDBPandasIOManager

from .resources import data_generator

from . import assets

datagen = data_generator.DataGeneratorResource(
    num_days=EnvVar.int("HACKERNEWS_NUM_DAYS_WINDOW"),
) # Make the resource

daily_refresh_schedule = ScheduleDefinition(
    job=define_asset_job(name="all_assets_job"), cron_schedule="0 0 * * *"
)

io_manager = FilesystemIOManager(
    base_dir = "data" # 相对路径，在 dagster dev 运行的文件夹下
)

# Insert this section anywhere above your `defs = Definitions(...)`
database_io_manager = DuckDBPandasIOManager(database="analytics.hackernews")

defs = Definitions(
    assets=load_assets_from_package_module(assets), 
    schedules=[daily_refresh_schedule],
    resources={
        "io_manager": io_manager,
        "database_io_manager": database_io_manager,  # Define the I/O manager here
        "hackernews_api": datagen, # Add the newly-made resource here
    },
)
