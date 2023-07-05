-- Refer to Using dbt with Dagster, part one for info about this file:
-- https://docs.dagster.io/integrations/dbt/using-dbt-with-dagster/part-one

select
    id as order_id,
    user_id as customer_id,
    order_date,
    status
from {{ source('jaffle_shop', 'orders_raw') }}