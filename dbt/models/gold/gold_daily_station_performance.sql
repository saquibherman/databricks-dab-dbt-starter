{{ config(alias="daily_station_performance") }}

select
    trip_start_date,
    start_station_name,
    {{ round_minutes("avg(trip_duration_mins)") }} as avg_trip_duration_mins,
    count(ride_id) as total_trips
from {{ source("silver", "jc_citibike") }}
group by trip_start_date, start_station_name
