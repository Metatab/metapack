{% if root.title -%}# {{root.title}}{%-endif%}
{% if root.name -%}`{{root.name}}`{%-else-%}`{{root.identifier}}`{%-endif%} Last Update: {{root.modified}}

_{{root.description}}_

{{inline_doc}}
{% if doc_links -%}
## Documentation Links
{% for title, doc in doc_links.items() %}
* [{{title}}]({{doc.url}}) {{doc.description}}
{%- endfor -%}
{% endif %}

 {# The doc_img alt text is so we can set a class for CSS to resize the image. img[alt=doc_img] { width: 100 px; } #}
{% if images -%}
## Images
{% for title, image in images.items() %}
[![doc_img]({{image.url}} "{{title}}")]({{image.url}})

{{image.description}}
{%- endfor -%}
{% endif -%}

{% if notes -%}
## Notes
{% for note in notes %}
* {{note | replace('\n', '')}}
{%- endfor -%}
{% endif -%}

{% if contacts %}
## Contacts
{% for term_name, terms in contacts.items() -%}
    {% for contact in terms %}
* **{{term_name|title}}** {{ contact.parts|join(', ')}}
{%- endfor %}
{%- endfor -%}
{% endif %}
{% if resources %}
## Resources
{% for term_name, terms in resources.items() -%}
    {% for resource in terms %}
* ** [{{resource.name}}]({{resource.url}})**. {{resource.description}}
{%- endfor %}
{%- endfor -%}
{% endif %}
{% if references %}
## References
<ul>{% for term_name, terms in references.items() -%}
{% for reference in terms %}
{%- if reference.url is not defined -%}
    NOPE!
{%- elif reference.url.startswith('http') -%}
    <li> <strong><a href="{{reference.url}}">{{reference.name}}</a></strong>. {{reference.description}}</li>
{%-else-%}
    <li> <strong>{{reference.name}}</string>, <em>{{reference.url}}</em>. {{reference.description}}</li>
{%-endif-%}
{%- endfor -%}
{%- endfor -%}<ul>
{% endif %}
