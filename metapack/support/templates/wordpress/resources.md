{% if resources %} 
<!-- wp:heading  -->
<h2 id="resources">Resources</h2>
<!-- /wp:heading -->

<!-- wp:paragraph  -->

<p>Direct access to individual CSV files.</p>
<!-- /wp:paragraph  -->

<!--wp:list -->

{% for term_name, terms in resources.items() -%}
{%- for resource in terms %}
* **[{{resource.name}}]({{resource.url}})**. {{resource.description}}
{%- endfor %}
{%- endfor %}

<!--/wp:list -->

{% endif %}