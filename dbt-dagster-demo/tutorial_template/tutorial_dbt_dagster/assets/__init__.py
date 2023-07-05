## Refer to Using dbt with Dagster, part two for info about this file:
## https://docs.dagster.io/integrations/dbt/using-dbt-with-dagster/part-two

import pandas as pd
import plotly.express as px
from dagster_dbt import load_assets_from_dbt_project

from dagster import AssetIn, MetadataValue, asset, file_relative_path


# 这里的 key_prefix 和后面引入 dbt 项目给定的 prefix 一致
@asset(key_prefix=["jaffle_shop"], group_name="staging")
def customers_raw() -> pd.DataFrame:
    """原始的 customers 信息，从 Dagster 网站下载
    
    用于展示如何将 dbt 与 dagster 结合
    """
    data = pd.read_csv("https://docs.dagster.io/assets/customers.csv")
    return data

@asset(key_prefix=["jaffle_shop"], group_name="staging")
def orders_raw() -> pd.DataFrame:
    """原始的 orders 信息，从 Dagster 网站下载
    
    用于展示如何将 dbt 与 dagster 结合
    """
    data = pd.read_csv("https://docs.dagster.io/assets/orders.csv")
    return data

# DBT 项目的位置
DBT_PROJECT_PATH = file_relative_path(__file__, "../../jaffle_shop")
# DBT 项目的配置文件的位置
DBT_PROFILES = file_relative_path(__file__, "../../jaffle_shop/config")

# 这是一种新的上游定义的方式，通过 `ins` 关键字
# 并且设置前缀为 `jaffle_shop`，组为 `staging`，这样和前面的 asset 保持一致
@asset(
    ins={"customers": AssetIn(key_prefix=["jaffle_shop"])},
    group_name="staging",
)
def order_count_chart(context, customers: pd.DataFrame) -> None:
    """绘制 order 数量的图表
    
    用于展示 dagster 如何引用 dbt 作为上游 asset
    """
    fig = px.histogram(customers, x="number_of_orders")
    fig.update_layout(bargap=0.2)
    save_chart_path = file_relative_path(__file__, "order_count_chart.html")
    fig.write_html(save_chart_path, auto_open=True)

    context.add_output_metadata({"plot_url": MetadataValue.url("file://" + save_chart_path)})


# 这里的 key_prefix 表示所有的 asset 会加上这个前缀，用于区分
dbt_assets = load_assets_from_dbt_project(
    project_dir=DBT_PROJECT_PATH, profiles_dir=DBT_PROFILES, key_prefix=["jaffle_shop"]
)