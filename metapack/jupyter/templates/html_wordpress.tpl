{%- extends 'basic.tpl' -%}

{%- block header -%}

    {%- if nb.metadata.frontmatter.description -%}
        <em>{{ nb.metadata.frontmatter.description }}</em>
    {% endif %}

    {%- for author in  nb.metadata.frontmatter.authors -%}
        <strong>{{ author.name }}</strong>{{ "," if not loop.last }}.
    {%- endfor -%}

    {%- if nb.metadata.frontmatter.github -%}
        <small><a href="{{ nb.metadata.frontmatter.github }}"> Full notebook on Github<i class="fa fa-github fa- "></i></small>
    {%- endif -%}

{%- endblock header -%}

{% block input_group -%}
{%- if cell.metadata.hide_input or nb.metadata.hide_input -%}
{%- else -%}
{{ super() }}
{%- endif -%}
{% endblock input_group %}

{% block output_group -%}
{%- if cell.metadata.hide_output -%}
{%- else -%}
    {{ super() }}
{%- endif -%}
{% endblock output_group %}

{% block output_area_prompt %}
{%- if cell.metadata.hide_input or nb.metadata.hide_input -%}
    <div class="prompt"> </div>
{%- else -%}
    {{ super() }}
{%- endif -%}
{% endblock output_area_prompt %}
