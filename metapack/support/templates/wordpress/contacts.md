{% if contacts %} 
<!-- wp:heading -->
<h2 id="contacts">Contacts</h2>
<!-- /wp:heading -->

<!-- wp:list -->

{% for term_name, terms in contacts.items() -%}
    {% for contact in terms %}
* **{{term_name|title}}** {{ contact.parts|join(', ')}} 
{%- endfor %}
{%- endfor %}

<!-- /wp:list -->

{% endif %}