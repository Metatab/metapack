{# The doc_img alt text is so we can set a class for CSS to resize the image. img[alt=doc_img] { width: 100 px; } #}
{% if images -%}

<!-- wp:heading -->

## Images
<!-- /wp:heading -->

<!-- wp:html -->
{% for title, image in images.items() %}
[![doc_img]({{image.url}} "{{title}}")]({{image.url}})

{{image.description}}
{%- endfor -%}

<!-- /wp:html -->

{% endif -%}