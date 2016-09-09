#!/usr/bin/env python

import osgeo
import osgeo.osr
from osgeo import ogr
import sys
import string
import os

debug = True

#
# Create and Define the Spatial Reference
#

if debug: print "Creating Spatial Reference"

spatialReference = osgeo.osr.SpatialReference() 
spatialReference.ImportFromProj4('+proj=utm +zone=17 +ellps=WGS84 +datum=WGS84 +units=m')

#
# Establish Driver for Shapefile
#

if debug: print "creating driver"

driverName =  "ESRI Shapefile"

driver = ogr.GetDriverByName( driverName )

if driver is None:
	print "Driver Not Available: %s" % driverName
	sys.exit( 1 )

if debug: print "creating dataSource"

path = "/opt/physical/util/kevdev/gis/shapefile/eden"
dataSource = driver.CreateDataSource( path )

if dataSource is None:
	print "Creation of DataSource output file FAILED"  
	sys.exit( 1 )

if debug: print "creating Layer"

#
# Create the Layer
# This will be the name of the shapefile that is written to the DataSource Directory
#

grid_layer = dataSource.CreateLayer( "grid_boundary", spatialReference, osgeo.ogr.wkbMultiPolygon )

if debug: print type( grid_layer )

grid_layer_defn = grid_layer.GetLayerDefn()

if debug: print "creating Geometry"
ring = osgeo.ogr.Geometry( osgeo.ogr.wkbLinearRing )

ring.AddPoint( 463200, 2790000 )
ring.AddPoint( 578000, 2790000 )
ring.AddPoint( 578000, 2952000 )
ring.AddPoint( 463200, 2952000 )
ring.AddPoint( 463200, 2790000 )

if debug: print "creating Polygone"

polygon1 = ogr.Geometry( ogr.wkbPolygon )
polygon1.AddGeometry( ring )

featureIndex = 0
feature = osgeo.ogr.Feature( grid_layer_defn )
feature.SetGeometry( polygon1 )
feature.SetFID( featureIndex )

if debug: print "adding feature to layer"

grid_layer.CreateFeature( feature )
		
dataSource.Destroy()
