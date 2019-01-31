{% if notes -%} 
<!-- wp:heading  -->
<h2 id="notes">Notes</h2>
<!-- /wp:heading -->

<!-- wp:list -->

{% for note in notes %}
* {{note | replace('\n', '')}}
{%- endfor %}

<!-- /wp:list -->

{% endif -%}
