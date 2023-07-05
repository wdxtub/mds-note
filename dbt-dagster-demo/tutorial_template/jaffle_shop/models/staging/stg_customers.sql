-- Refer to Using dbt with Dagster, part one for info about this file:
-- https://docs.dagster.io/integrations/dbt/using-dbt-with-dagster/part-one

select
    id as customer_id,
    first_name,
    last_name
from {{ source('jaffle_shop', 'customers_raw') }}