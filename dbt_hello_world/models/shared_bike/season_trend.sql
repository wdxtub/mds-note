/* 季节趋势表 */

{{ config(materialized='table') }}

with season_trend as (
    select season, min(temp*47+8) as min_temp, max(temp*47+8) as max_temp, avg(temp*47+8) as mean_temp, sum(casual) as total_casual, sum(registered) as total_registered, sum(cnt) as total_cnt
    from {{ ref('day') }}
    group by season
)

select * from season_trend