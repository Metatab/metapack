{%- extends 'basic.tpl' -%}

{%- block header -%}

{%- for author in  nb.metadata.frontmatter.authors -%}
<!-- wp:paragraph -->
<p><strong>{{ author.name }}</strong>{{ "," if not loop.last }}.</p>
<!-- /wp:paragraph -->
{%- endfor -%}
{%- if nb.metadata.frontmatter.description -%}
<!-- wp:paragraph -->
<p><em>{{ nb.metadata.frontmatter.description }}</em></p>
<!-- /wp:paragraph -->
{% endif %}
{%- if nb.metadata.frontmatter.github -%}
<!-- wp:button {"backgroundColor":"cyan-bluish-gray","className":"is-style-squared"} -->
<div class="wp-block-button is-style-squared">
<a class="wp-block-button__link has-background has-cyan-bluish-gray-background-color" 
   href="{{ nb.metadata.frontmatter.github }}">
 <code>[icon name="github" class="icon-2x"]</code> 
 Full notebook on github<br></a>
 </div>
<!-- /wp:button -->
{%- endif -%}

{%- endblock header -%}

{% block in_prompt %}
{% endblock in_prompt %}


{% block input_group -%}
{%- if cell.metadata.hide_input or nb.metadata.hide_input -%}
{%- else -%}
<!-- wp:code -->
<pre class="wp-block-code"><code>{{ cell.source }}</code></pre>
<!-- /wp:code -->
{%- endif -%}
{% endblock input_group %}


{% block output_group -%}
{%- if cell.metadata.hide_output -%}
{%- else -%}
<!-- wp:html -->
{{ super() }}
<!-- /wp:html -->
{%- endif -%}
{% endblock output_group %}

{% block output_area_prompt %}
{% endblock output_area_prompt %}
