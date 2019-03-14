<!-- wp:paragraph -->
<p id="top"><em>{{root.description}}</em></p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->

{% if root.name -%}`{{root.name}}`{%-else-%}`{{root.identifier}}`{%-endif%} 

<!-- /wp:paragraph -->
<!-- wp:html -->
<p><a href="#resources">Resources</a> | <a href="#packages">Packages</a> | <a href="#documentation">Documentation</a>
{%- if contacts -%} | <a href="#contacts">Contacts</a>{%- endif -%}
{%- if references -%} | <a href="#references">References</a>{%- endif -%}</p>
<!-- /wp:html -->