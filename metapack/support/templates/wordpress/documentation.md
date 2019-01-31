<!-- wp:heading  -->
<h2 id="documentation">Documentation</h2>
<!-- /wp:heading -->

<!-- wp:html -->

{{inline_doc}}

<!-- /wp:html -->

{% if doc_links -%}
<!-- wp:heading  -->
<h3 id="documentation_links">Documentation Links</h3>
<!-- /wp:heading -->
<!-- wp:list -->
{% for title, doc in doc_links.items() %}
* [{{title}}]({{doc.url}}) {{doc.description}}
{%- endfor %}


<!-- /wp:list -->
{% endif %}