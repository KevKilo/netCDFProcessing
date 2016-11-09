#!/usr/bin/env python

#
# avg many shapfiles to make, in this first case, an average May water level
#


import os
import sys

from osgeo import ogr
from osgeo import osr

import numpy
import datetime
import time
import Scientific.IO.NetCDF
from Scientific.IO.NetCDF import NetCDFFile
from scipy import stats

# create list of shapeFiles
#

deBug = False

##shapeFileDir = "/physical/util/shapeFiles/"
##shapeFileDir = "/physical/gis/eden/recovery/"
shapeFileDir = "/physical/gis/eden/May/"

# no. of rows ans columns in the eden grid
#
nrow = 405
ncol = 287

# set for max number of shapefiles to aggregate
# e.g only 31 days in May, but we are looking at 16 Mays from 2000 to 2015

ndays = 500 

# create arrrays
#

depth = numpy.zeros( ( 500, 405, 287 ), 'f' )
stage = numpy.zeros( ( 500, 405, 287 ), 'f' )

depthAvg = numpy.zeros( ( 405, 287 ), 'f' )
stageAvg = numpy.zeros( ( 405, 287 ), 'f' )

# get file list
#

##systring = "ls " + shapeFileDir + "eden_epa20000501.shp"
systring = "ls " + shapeFileDir + "*.shp"

print systring

shapeFileList = os.popen( systring, 'r' )

day = 0


for line in shapeFileList.readlines():

        rowList = []
        colList = []

	shapefile = line.rstrip()

        print "Opening %s" % shapefile

	driver = ogr.GetDriverByName("ESRI Shapefile")
	dataSource = driver.Open(shapefile, 0)
	layer = dataSource.GetLayer()

	for feature in layer:
    		currentRow = feature.GetFieldAsInteger( "row" )
    		currentCol = feature.GetFieldAsInteger( "col" )
    		currentWaterDepth = feature.GetFieldAsDouble( "WaterDepth" )
    		currentStage = feature.GetFieldAsDouble( "Stage" )

		rowList.append( currentRow )
		colList.append( currentCol )

		if deBug: print "Row: %d"  % currentRow
		if deBug: print "Cow: %d"  % currentCol
		if deBug: print "Depth: %f"  % currentWaterDepth
		if deBug: print "Stage: %f"  % currentStage

		depth[ day, currentRow, currentCol ] = currentWaterDepth
		stage[ day, currentRow, currentCol ] = currentStage

	day = day + 1		

print "day: %d" % day

# Populate array of average stage and average depth from all the shape files
# processed
#

print "no. rows: %d" % ( len( rowList ) )
print "no. cols: %d" % ( len( colList ) )

for i in range( 0, 46818 ):

	stageAvg[ rowList[ i ], colList[ i ] ] = numpy.mean( stage[ 0:day:1, rowList[ i ], colList[ i ] ] )
	depthAvg[ rowList[ i ], colList[ i ] ] = numpy.mean( depth[ 0:day:1, rowList[ i ], colList[ i ] ] )

##	if deBug: print "Avg stage: %f" % ( stageAvg[ i, j ] )
##	if deBug: print "Avg depth: %f" % ( depthAvg[ i, j ] )
##	if deBug: print "row: %d\ncol: %d" % ( i,  j )

# Open lsel file to use as a mask
#

netcdf_lsel_filename = "/opt/physical/agency_data/eden/dem/eden_dem_cm_oc11.nc"
lsel_input =  NetCDFFile( netcdf_lsel_filename, 'r' )

lsel = lsel_input.variables[ 'dem' ][ : ]

# Begin creating shapefile
#

# Create Spatial Reference
#

spatialReference = osr.SpatialReference()
spatialReference.ImportFromProj4( '+proj=utm +zone=17 +ellps=WGS84 +datum=WGS84 +units=m')

# Create Driver
#

outDriver = ogr.GetDriverByName( "ESRI Shapefile" )

# Create Layer
#

if deBug: print "Creating Final Layer"

outLayerName = "edenEpaAvg" 
outDirName = shapeFileDir + "avg/" 
outPathBaseName = outDirName  + outLayerName 
outPathShapeName = outDirName +  outLayerName + ".shp"

# Delete shapefile if it exists
#
 
if os.path.isfile( outPathShapeName ):

        print "File exists, must be deleted: %s" % outPathShapeName 
        systring = "rm " + outPathBaseName + ".*"

        if ( os.system( systring ) ) == 0:
                print "file deleted"
        else: print "could not delete file"

# Create Data Source: the directory where the shapefile goes (operates on driver)
#

if deBug: print "Creating outDataSource"

outDataSource = outDriver.CreateDataSource( outDirName )  

# Create Layer: names the shapefie (depends on spatial reference)
#

if deBug: print "Creating gridLayer"
outGrid_layer = outDataSource.CreateLayer( outLayerName, spatialReference, ogr.wkbMultiPolygon )

# Define Feature attributes
#

if deBug: print "Defining Feature Attributes"
# Define the fields objects
#
field_row = ogr.FieldDefn( "row", ogr.OFTInteger )
field_col = ogr.FieldDefn( "col", ogr.OFTInteger )
field_Stage = ogr.FieldDefn( "Stage", ogr.OFTReal )
field_WaterDepth = ogr.FieldDefn( "WaterDepth", ogr.OFTReal )

# Add Feature Attributes to Layer (i.e. to the shapefile)
#

if deBug: print "Creating Fields"
outGrid_layer.CreateField( field_row )
outGrid_layer.CreateField( field_col )
outGrid_layer.CreateField( field_Stage )
outGrid_layer.CreateField( field_WaterDepth )

# Create Layer Definition: This is needed to create each individual feature
# in the layer
# 

outGrid_layer_defn = outGrid_layer.GetLayerDefn()

if deBug: print "creating Geometry"

left_edge_x = 463200
bottom_edge_y = 2790000

start_y = bottom_edge_y

for i in range( 0, nrow):
        start_x = left_edge_x - 400
        start_y = bottom_edge_y + ( i * 400 )

        for j in range( 0, ncol ):
                start_x += 400

# the entire rectagular domain is not populated with data, so we use a mask
# from the lsel file and skip the record 

                if numpy.isnan( lsel[ i, j ]):
                        continue
                                
                feature = ogr.Feature( outGrid_layer_defn )

                feature.SetField( "WaterDepth", float( depthAvg[ i, j ] ) )
                feature.SetField( "Stage", float( stageAvg[ i, j ] ) )
# 
# Fields of the feature are set individually, then destroyed
# the new one is created above with the same outGrid_layer_defn...
# i think?

                feature.SetField( "row", i )
                feature.SetField( "col", j )

                ring = ogr.Geometry( ogr.wkbLinearRing )

                ring.AddPoint( start_x, start_y )
                ring.AddPoint( start_x + 400, start_y )
                ring.AddPoint( start_x + 400, start_y + 400 )
                ring.AddPoint( start_x, start_y + 400 )
                ring.AddPoint( start_x, start_y )
                cell = ogr.Geometry( ogr.wkbPolygon )
                cell.AddGeometry( ring )

                feature.SetGeometry( cell )

                outGrid_layer.CreateFeature( feature )

                feature.Destroy()





