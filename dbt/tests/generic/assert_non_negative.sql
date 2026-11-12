{#- Generic test: fails for rows where the column is negative. -#}
{% test assert_non_negative(model, column_name) %}

    select * from {{ model }} where {{ column_name }} < 0

{% endtest %}
