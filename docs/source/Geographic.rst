


For Geographic datafiles, You can add a Datafile.Projection property to set the
projection. If it specifies a particular projection, it must be an EPSG value,
prefixed with 'epsg:', such as: 'epsg:4269'. If this projection is different
than the soruce, the data will be projected while it is loaded.

The value can also be specified as '<source>", in which case the data will not
be projected, and the `Datafile.Projection` value will be replaced with the
source projection code in built packages. THe property will be added to the
Datafile term if it does not exist.

