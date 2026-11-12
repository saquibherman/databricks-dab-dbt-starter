{#- Round a duration (in minutes) to 2 decimals, matching the original PySpark gold notebooks. -#}
{% macro round_minutes(expression, decimal_places=2) -%}
    round({{ expression }}, {{ decimal_places }})
{%- endmacro %}
