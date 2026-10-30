{# Override of dbt-duckdb's macro: a model's `external_root` config (set per folder in dbt_project.yml)
   takes precedence over the profile's external_root. #}
{%- macro external_location(relation, config) -%}
  {%- set root = config.get('external_root', adapter.external_root()) -%}
  {%- if config.get('options', {}).get('partition_by') is none -%}
    {%- set format = config.get('format', 'parquet') -%}
    {{- root }}/{{ relation.identifier }}.{{ format }}
  {%- else -%}
    {{- root }}/{{ relation.identifier }}
  {%- endif -%}
{%- endmacro -%}
