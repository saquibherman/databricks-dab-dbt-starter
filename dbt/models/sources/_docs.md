{% docs silver_jc_citibike %}

Cleaned Citi Bike trips for Jersey City, one row per ride.

| Column               | Description                                       |
|----------------------|---------------------------------------------------|
| ride_id              | Primary key                                       |
| trip_start_date      | Date the ride started                             |
| started_at           | Ride start timestamp                              |
| ended_at             | Ride end timestamp                                |
| start_station_name   | Start station                                     |
| end_station_name     | End station                                       |
| trip_duration_mins   | Ride duration in minutes                          |
| metadata             | Map with pipeline_id, run_id, task_id, processed_timestamp |

{% enddocs %}

{% docs gold_daily_ride_summary %}

Daily ride statistics across all stations: min / max / average trip duration
(minutes, rounded to 2 decimals) and the number of trips. One row per `trip_start_date`.

{% enddocs %}

{% docs gold_daily_station_performance %}

Daily performance per start station: average trip duration (minutes, rounded to 2 decimals)
and number of trips. One row per `trip_start_date` and `start_station_name`.

{% enddocs %}
