{{ config(alias="daily_ride_summary") }}

select
    trip_start_date,
    {{ round_minutes("max(trip_duration_mins)") }} as max_trip_duration_mins,
    {{ round_minutes("min(trip_duration_mins)") }} as min_trip_duration_mins,
    {{ round_minutes("avg(trip_duration_mins)") }} as avg_trip_duration_mins,
    count(ride_id) as total_trips
from {{ source("silver", "jc_citibike") }}
group by trip_start_date
