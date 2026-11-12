{#-
    Use a model's custom schema as-is (e.g. `03_gold`) instead of dbt's default
    `<target_schema>_<custom_schema>`, so dbt writes to the same schemas as the notebooks.
-#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%} {{ target.schema }}
    {%- else -%} {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
