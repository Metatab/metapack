{% if references %} 
<!-- wp:heading -->
<h2 id="references">References</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->

<p>Urls used in the creation of this data package.</p>
<!-- /wp:paragraph -->

<!-- wp:list -->

{% for term_name, terms in references.items() -%}
{% for reference in terms %}
* **{%- if reference.url.startswith('http') -%}[{{reference.name}}]({{reference.url}})
{%-else-%}{{reference.url}}{%-endif-%}**. 
{{reference.description}}
{%- endfor %}
{%- endfor %}

<!-- /wp:list -->

{% endif %}