# Copyright (c) 2016 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""
Create Markdown and HTML of datasets. most importantly, Create a documentation context data structure,
a data structure that can be used to generate documentation, such as a jira2 context
"""

import datetime

from markdown import markdown as convert_markdown
from metatab.doc import MetatabDoc
from nameparser import HumanName
from pybtex import PybtexEngine
from pybtex.backends.html import Backend as HtmlBackend
from pybtex.style.formatting import toplevel
from pybtex.style.formatting.plain import Style
from pybtex.style.template import (
    field,
    href,
    optional,
    optional_field,
    sentence,
    together,
    words
)
from rowgenerators import parse_app_url
from yaml import safe_dump

from metapack.exc import PackageError

dl_templ = "{}\n:   {}\n\n"


def ns(v):
    """Return empty str if bool false"""
    return str(v) if bool(v) else ''


def linkify(v, description=None, cwd_url=None):
    if not v:
        return None

    u = parse_app_url(v)

    if u.scheme in ('http', 'https', 'mailto'):

        if description is None:
            description = v
        return '[{desc}]({url})'.format(url=v, desc=description)

    elif u.scheme == 'file':

        return '[{desc}]({url})'.format(url=u.path, desc=description)

    else:
        return v


def resource(r, fields=None):
    fields = fields or (
        ('Header', 'header'),
        ('Datatype', 'datatype'),
        ('Description', 'description')
    )

    headers = [f[0] for f in fields]
    keys = [f[1] for f in fields]

    rows = [''.join(["<td>{}</td>".format(e.replace("\n", "<br/>\n")) for e in [c.get(k, '') for k in keys]])
            for c in r.columns()]

    return ("### {name} \n [{url}]({url})\n\n".format(name=r.name, url=r.resolved_url)) + \
            "{}\n".format(ns(r.description)) + \
            "<table class=\"table table-striped\">\n" + \
           ("<tr>{}</tr>".format(''.join("<th>{}</th>".format(e) for e in headers))) + \
            "\n".join("<tr>{}</tr>".format(row) for row in rows) + \
            '</table>\n'

def ckan_resource_markdown(r, fields=None):
    fields = fields or (
        ('Header', 'header'),
        ('Datatype', 'datatype'),
        ('Description', 'description')
    )

    # headers = [f[0] for f in fields]
    # keys = [f[1] for f in fields]

    def col_line(c):
        return "* **{}** ({}): {}\n".format(
            c.get('header'),
            c.get('datatype'),
            "*{}*".format(c.get('description')) if c.get('description') else '')

    return "### {}. {} Columns. \n\n{}".format(
        ns(r.description),
        len(list(r.columns())),
        ''.join([col_line(c) for c in r.columns()])
    )


def resource_block(doc, fields=None):
    if fields is None:
        fields = [
            ('Header', 'header'),
            ('Datatype', 'datatype'),
            ('Description', 'description')
        ]

        for h in doc['Schema'].args:

            if h.lower() in ('note', 'notes', 'coding'):
                fields.append((h, h.lower()))

    return "".join(resource(r, fields) for r in doc['Resources'].find('Root.Resource'))


def resource_ref(r):
    return dl_templ.format(r.name, "_{}_<br/>{}".format(r.resolved_url, ns(r.description)))


def resource_ref_block(doc):
    return "".join(resource_ref(r) for r in doc['Resources'].find('Root.Resource'))


def contact(r):
    pass


class MetatabStyle(Style):
    # Minnesota Population Center. IPUMS Higher Ed: Version 1.0 [dataset]
    # Minneapolis, MN: University of Minnesota, 2016. http://doi.org/10.18128/D100.V1.0.

    def format_url(self, e):
        return words[
            href[
                field('url', raw=True),
                field('url', raw=True)
            ]
        ]

    def format_accessed(self, e):
        from dateutil.parser import parser

        return words[
            'Accessed',
            field('accessdate', raw=True, apply_func=lambda v: str(parser().parse(v).strftime("%d %b %Y")))
        ]

    def format_dataset(self, e):
        template = toplevel[
            optional[sentence[field('origin')]],
            self.format_btitle(e, 'title'),
            optional[sentence[together['Version', field('version')]]],
            optional[sentence[field('publisher')]],
            optional[self.format_author_or_editor(e)],
            optional[words[optional_field('month'), field('year')]],
            self.format_web_refs(e),
            self.format_accessed(e)
        ]

        return template.format_data(e)


class MetatabHtmlBackend(HtmlBackend):
    def write_prologue(self):
        pass
        # super().write_prologue()

    def write_epilogue(self):
        pass
        # super().write_epilogue()

    def write_entry(self, key, label, text):
        self.output("<div class='citation'><a name=\"{key}\"><b>[{key}]</b></a> {text} </div>"
                    .format(key=key, text=text))


def make_citation_dict(td):
    """
    Update a citation dictionary by editing the Author field
    :param td: A BixTex format citation dict or a term
    :return:
    """

    from datetime import datetime

    if isinstance(td, dict):
        d = td

    else:

        d = td.as_dict()
        d['_term'] = td

        try:
            d['name_link'] = td.name
        except AttributeError:
            d['name_link'] = td['name_link'].value

    if 'author' in d and isinstance(d['author'], str):
        authors = []
        for e in d['author'].split(';'):
            author_d = HumanName(e).as_dict(include_empty=False)
            if 'suffix' in author_d:
                author_d['lineage'] = author_d['suffix']
                del author_d['suffix']
            authors.append(author_d)
        d['author'] = authors

    if 'type' not in d:

        if '_term' in d:
            t = d['_term']

            if t.term_is('Root.Reference') or t.term_is('Root.Resource'):
                d['type'] = 'dataset'

            elif t.term_is('Root.Citation'):
                d['type'] = 'article'
            else:
                d['type'] = 'article'

    if d['type'] == 'dataset':

        if 'editor' not in d:
            d['editor'] = [HumanName('Missing Editor').as_dict(include_empty=False)]

        if 'accessdate' not in d:
            d['accessdate'] = datetime.now().strftime('%Y-%m-%d')

    if 'author' not in d:
        d['author'] = [HumanName('Missing Author').as_dict(include_empty=False)]

    if 'title' not in d:
        d['title'] = d.get('description', '<Missing Title>')

    if 'journal' not in d:
        d['journal'] = '<Missing Journal>'

    if 'year' not in d:
        d['year'] = '<Missing Year>'

    if '_term' in d:
        del d['_term']

    return d


def make_metatab_citation_dict(t):
    """
    Return a dict with BibText key/values for metatab data
    :param t:
    :return:
    """

    try:

        if parse_app_url(t.url).proto == 'metatab':

            try:
                url = parse_app_url(str(t.resolved_url)).resource_url
                doc = t.row_generator.generator.package

            except AttributeError:
                return False  # It isn't a resource or reference

            creator = doc.find_first('Root.Creator')
            author_key = 'author'

            if not creator:
                creator = doc.find_first('Root.Wrangler')
                author_key = 'editor'

            if not creator:
                creator = doc.find_first('Root.Origin')
                author_key = 'editor'

            try:
                origin = doc['Contacts'].get('Root.Origin').get('organization').value
            except AttributeError:
                try:
                    origin = doc.get_value('Root.Origin', doc.get_value('Name.Origin')).title()
                except Exception:
                    origin = None

            d = {
                'type': 'dataset',
                'name_link': t.name,
                author_key: [HumanName(creator.value).as_dict(include_empty=False)],
                'publisher': creator.properties.get('organization'),
                'origin': origin,
                'journal': '2010 - 2015 American Community Survey',
                'title': doc['Root'].find_first_value('Root.Title') + '; ' + t.name,
                'year': doc.get_value('Root.Year'),
                'accessDate': '{}'.format(datetime.datetime.now().strftime('%Y-%m-%d')),
                'url': url,
                'version': doc.get_value('Root.Version', doc.get_value('Name.Version')),
            }

            d = {k: v for k, v in d.items() if v is not None}

            return d


        else:
            return False

    except (AttributeError, KeyError):
        raise
        return False


def _bibliography(doc, terms, converters=[], format='html'):
    """
    Render citations, from a document or a doct of dicts

    If the input is a dict, each key is the name of the citation, and the value is a BibTex
    formatted dict

    :param doc: A MetatabDoc, or a dict of BibTex dicts
    :return:
    """

    output_backend = 'latex' if format == 'latex' else MetatabHtmlBackend

    def mk_cite(v):
        for c in converters:
            r = c(v)

            if r is not False:
                return r

        return make_citation_dict(v)

    if isinstance(doc, MetatabDoc):
        # This doesn't work for LaTex, b/c the formatter adds the prologue and epilogue to eery entry

        d = [mk_cite(t) for t in terms]

        cd = {e['name_link']: e for e in d}

    else:

        cd = {k: mk_cite(v, i) for i, (k, v) in enumerate(doc.items())}

    return PybtexEngine().format_from_string(safe_dump({'entries': cd}),
                                             style=MetatabStyle,
                                             output_backend=output_backend,
                                             bib_format='yaml')


def bibliography(doc, converters=[], format='html'):
    terms = list(doc.get_section('Bibliography', []))

    return _bibliography(doc, terms, converters, format)


def data_sources(doc, converters=[], format='html'):
    terms = list(doc.references()) + list(doc.resources())

    return _bibliography(doc, terms, converters, format)


def identity_block(doc):
    from collections import OrderedDict

    name = doc.find_first('Root.Name')

    d = OrderedDict(
        name=name.value,
        identifier=doc.find_first_value('Root.Identifier'),
    )

    for k, v in name.props.items():
        d[k] = v

    try:
        del d['@value']
    except KeyError:
        pass

    return "".join(dl_templ.format(k, v) for k, v in d.items())


def modtime_str(doc):
    from dateutil.parser import parse

    modtime = doc.find_first_value('Root.Modified') or doc.find_first_value('Root.Issued')

    if modtime:
        try:
            modtime_str = "Last Modified: " + parse(modtime).strftime("%Y-%m-%d %H:%M")
        except ValueError:
            modtime_str = ''

    else:

        modtime_str = ''

    return modtime_str


def process_contact(d):
    email = d.get('email', None)
    org = d.get('organization', None)
    url = d.get('url', None)
    name = d.get('name', None)

    if name and email and org and url:
        return {
            'parts': ["[{}]({})".format(name, 'mailto:' + email), "[{}]({})".format(org, url)]
        }

    elif name and email and org:
        return {
            'parts': ["[{}]({})".format(name, 'mailto:' + email), "{}".format(org)]
        }
    elif name and email and url:
        return {
            'parts': ["[{}]({})".format(name, 'mailto:' + email), "{}".format(url)]
        }

    elif name and org and url:
        return {
            'parts': ["{}".format(name), "[{}]({})".format(org, url)]
        }

    elif name and org:
        return {
            'parts': ["{}".format(name), "{}".format(org)]
        }
    elif name and url:
        return {
            'parts': ["{}".format(name), "[{}]({})".format(url, url)]
        }
    elif name and email:
        return {
            'parts': ["[{}]({})".format(name, 'mailto:' + email)]
        }
    elif name:
        return {
            'parts': ["{}".format(name)]
        }
    elif org and email and url:
        return {
            'parts': ["[{}]({})".format(org, url), "[{}]({})".format(email, 'mailto:' + email)]
        }
    elif org and email:
        return {
            'parts': ["{}".format(org), "[{}]({})".format(email, 'mailto:' + email)]
        }
    elif org and url:
        return {
            'parts': ["[{}]({})".format(org, url)]
        }
    elif url and email:
        return {
            'parts': ["[{}]({})".format(url, url), "[{}]({})".format(email, 'mailto:' + email)]
        }

    elif org:
        return {
            'parts': ["{}".format(org)]
        }
    elif url:
        return {
            'parts': ["[{}]({})".format(url, url)]
        }
    elif email:
        return {
            'parts': ["[{}]({})".format(email, 'mailto:' + email)]
        }
    else:

        return {
            'parts': []
        }


def process_contacts_html(d):
    pc = process_contact(d)

    pc['html'] = convert_markdown(', '.join(pc['parts']))

    return pc


def display_context(doc):
    """Create a Jinja context for display"""
    from rowgenerators.exceptions import DownloadError

    # Make a naive dictionary conversion
    context = {s.name.lower(): s.as_dict() for s in doc if s.name.lower() != 'schema'}

    mandatory_sections = ['documentation', 'contacts']

    # Remove section names
    deletes = []
    for k, v in context.items():
        try:
            del v['@value']
        except KeyError:
            pass  # Doesn't have the value
        except TypeError:
            # Is actually completely empty, and has a scalar value. Delete and re-create
            deletes.append(k)

        if isinstance(v, str):  # Shouldn't ever happen, but who knows ?
            deletes.append(k)

    for d in deletes:
        try:
            del context[d]
        except KeyError:
            # Fails in TravisCI, no idea why.
            pass

    for ms in mandatory_sections:
        if ms not in context:
            context[ms] = {}

    # Load inline documentation
    inline = ''

    for d in context.get('documentation', {}).get('documentation', []):

        try:
            u = parse_app_url(d['url'])
        except TypeError:
            continue

        if u.target_format == 'md':  # The README.md file
            inline = ''

            if u.proto == 'file':
                # File really ought to be relative
                t = doc.package_url.join_target(u).get_resource().get_target()
            else:
                try:
                    t = u.get_resource().get_target()
                except DownloadError as e:
                    raise e

            try:

                with open(t.fspath) as f:
                    inline += f.read()

            except FileNotFoundError:
                pass

            del d['title']  # Will cause it to be ignored in next section

    # Strip off the leading title, if it exists, because it will be re-applied
    # by the templates

    lines = inline.strip().splitlines()
    if lines and lines[0].startswith('# '):
        lines = lines[1:]

    context['inline_doc'] = '\n'.join(lines)

    # Convert doc section
    doc_links = {}
    images = {}
    for term_name, terms in context['documentation'].items():
        if term_name == 'note':
            context['notes'] = terms
        elif terms:
            for i, term in enumerate(terms):
                try:
                    if term_name == 'image':
                        images[term['title']] = term
                    else:
                        doc_links[term['title']] = term
                except AttributeError:  # A scalar
                    pass  # There should not be any scalars in the documentation section
                except KeyError:
                    pass  # ignore entries without titles
                except TypeError:
                    pass  # Also probably a ascalar

    context['doc_links'] = doc_links
    context['images'] = images

    del context['documentation']

    #
    # Update contacts

    origin = None
    for term_name, terms in context['contacts'].items():
        if isinstance(terms, dict):
            origin = terms  # Origin is a scalar in roort, must be converted to sequence here
        else:
            for t in terms:
                try:
                    t.update(process_contacts_html(t))
                except AttributeError:
                    pass  # Probably got a scalar
    if origin:
        origin.update(process_contacts_html(origin))
        context['contacts']['origin'] = [origin]

    # For resources and references, convert scalars into lists of dicts, which are the
    # default for Datafiles and References.

    for section in ('references', 'resources'):
        if section not in context:
            context[section] = {}
        for term_key, term_vals in context[section].items():
            if isinstance(term_vals, dict):
                if '@value' in term_vals:
                    term_vals['url'] = term_vals['@value']
                    del term_vals['@value']
                new_term_vals = [term_vals]
            elif isinstance(term_vals, list):
                new_term_vals = None
            else:
                new_term_vals = [{'url': term_vals, 'name': term_vals}]

            if new_term_vals:
                context[section][term_key] = new_term_vals

    # Add in other properties to the resources
    for term in context.get('resources', {}).get('datafile', []):

        r = doc.resource(term['name'])
        if r is not None:
            term['isgeo'] = r.isgeo

    context['distributions'] = {}
    for dist in doc.find('Root.Distribution'):
        context['distributions'][dist.type] = dist.value

    if doc.find('Root.Giturl'):
        context['distributions']['source'] = doc.get_value('Root.Giturl')

    context['schema'] = {}
    if 'Schema' in doc:
        for t in doc['Schema'].find('Root.Table'):
            context['schema'][t.name] = []
            for c in t.find('Table.Column'):
                context['schema'][t.name].append(c.as_dict())

    return context


def markdown(doc, title=True, template='short_documentation.md'):
    """Markdown, specifically for the Notes field in a CKAN dataset"""

    from jinja2 import Environment, PackageLoader
    env = Environment(
        loader=PackageLoader('metapack', 'support/templates')
        # autoescape=select_autoescape(['html', 'xml'])
    )

    context = display_context(doc)

    return env.get_template(template).render(**context)


def html(doc, template='short_documentation.md'):
    extensions = [
        'markdown.extensions.extra',
        'markdown.extensions.admonition'
    ]

    return """
<html>
<head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <!-- Latest compiled and minified CSS -->
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css" integrity="sha384-BVYiiSIFeK1dGmJRAkycuHAHRg32OmUcww7on3RYdg4Va+PmSTsz/K68vbdEjh4u" crossorigin="anonymous">

    <!-- Optional theme -->
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap-theme.min.css" integrity="sha384-rHyoN1iRsVXV4nD0JutlnGaslCJuC7uwjduW9SVrLvRYooPp2bWYgmgJQIXwl/Sp" crossorigin="anonymous">

    <style>
    .narrow-dl .dl-horizontal dd {{
        margin-left: 100px;
    }}

    img[alt=doc_img] {{ width: 300px; }}

    .narrow-dl .dl-horizontal dt {{
        width: 80px;
    }}

    </style>
    <title>{title}</title>
</head>
<body>
    <div class="container">
        <div class="row">
            {body}
        </div>
    </div>
</body>
</html>
    """.format(
        title=doc.find_first_value('Root.Title'),
        body=convert_markdown(markdown(doc, template=template), extensions=extensions)
    )


def jsonld(doc):
    """Produce JSONLD with a Dataset schema, to have web pages with the
    dataset properly indexed by Google"""

    context = display_context(doc)

    """
<script type="application/ld+json">
{
  "@context" : "http://schema.org",
  "@type" : "Dataset",
  "name" : "Child",
  "description" : "The Child and Adult Care Food Program (CACFP) provides federal funding to participating child care and adult day care centers, allowing the centers to serve nutritious meals to enrolled participants",
  "version" : "cde.ca.gov-cacfp_sites-2",
  "distribution" : {
    "@type" : "DataDownload",
    "encodingFormat" : "csv",
    "contentUrl" : "http://library.metatab.org/cde.ca.gov-cacfp_sites-2/data/cacfp_sites.csv"
  },
  "sourceOrganization" : "Eric",
  "datePublished" : "2019-06-18T04:34:22"
}
</script>
"""

    root = context.get('root')

    if not root:
        raise PackageError('Could not get root from display context')

    d = {
        "@context": "http://schema.org",
        "@type": "Dataset",
        "name": root.get('title'),
        "version": root.get('name'),
        "alternateName": root.get('name'),
        "description": root.get('description'),
        "identifier": [
            root.get('identifier'),
            root.get('name')
        ]
    }

    issued = root.get('issued')

    if issued:
        d['datePublished'] = issued

    distributions = []

    for typ, url in context.get('distributions', {}).items():
        if typ in ('csv', 'zip'):
            distributions.append({
                '@type': 'DataDownload',
                'encodingFormat': typ,
                'contentUrl': url
            })

    # Do it later
    for typ, v in context.get('contacts', {}).items():
        pass

    d['distribution'] = distributions

    return d
