<!-- wp:heading  -->
<h2 id="packages">Packages</h2>
<!-- /wp:heading -->

<!-- wp:paragraph  -->

Collections of all files in the dataset. ZIP packages have all files and documentation in a ZIP file and are compressed to load faster. 
Excel files have all data in worksheet tabs. CSV packages reference files stored on the net, and are best for use
with analysis tools like Metapack. 

<!-- /wp:paragraph  -->
	
<!-- wp:list -->

{% for pkg_type, pkg_url in distributions.items() %}
{% if pkg_type != 'fs' %}* **{{pkg_type}}** [{{pkg_url}}]({{pkg_url}}){% endif %}
{%- endfor %}

<!-- /wp:list -->

{% if distributions.zip  or distributions.csv %}
<!-- wp:heading  -->
<h3 id="metapack">Accessing Packages in Metapack</h3>
<!-- /wp:heading -->
<!-- wp:code -->
<pre class="wp-block-code"><code>import metapack as mp
{% if distributions.zip %}# ZIP Package
pkg = mp.open_package('{{distributions.zip}}'){% endif %}
{% if distributions.csv %}# CSV Package
pkg = mp.open_package('{{distributions.csv}}') {% endif %}

resource = pkg.resource('resource_name') # Get a resource
df = resource.dataframe() # Create a pandas Dataframe
gdf = resource.geoframe() # Create a GeoPandas GeoDataFrame
</code></pre>
<!-- /wp:code -->
{%- endif %}
