#!/usr/bin/env python

#
# take the difference of stage and depth from two shapefiles
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

#
#       sort out argv
#

if len(sys.argv) <> 3:

        sys.exit("\nUsage: %s shapeFilePositive shapeFileNegative\n" % sys.argv[0])

shapeFileNamePos = sys.argv[ 1 ]
shapeFileNameNeg = sys.argv[ 2 ]

# create list of shapeFiles
#

deBug = True

# no. of rows ans columns in the eden grid

nrow = 405
ncol = 287

# create arrrays
# one for the positive values and one for the negative values

stagePos = numpy.zeros( ( 405, 287 ), 'f' )
depthPos = numpy.zeros( ( 405, 287 ), 'f' )

depthNeg = numpy.zeros( ( 405, 287 ), 'f' )
stageNeg = numpy.zeros( ( 405, 287 ), 'f' )

depthDiff = numpy.zeros( ( 405, 287 ), 'f' )
stageDiff = numpy.zeros( ( 405, 287 ), 'f' )

rowListPos = []
colListPos = []

rowListNeg = []
colListNeg = []


print "Opening\n%s\n%s" % ( shapeFileNamePos, shapeFileNameNeg )

driver = ogr.GetDriverByName( "ESRI Shapefile" )

dataSourcePos = driver.CreateDataSource( shapeFileNamePos )
dataSourceNeg = driver.CreateDataSource( shapeFileNameNeg )

print type( dataSourcePos )
print type( dataSourceNeg )

layerPos = dataSourcePos.CreateLayer()
layerNeg = dataSourceNeg.CreateLayer()

for feature in layerPos:
	currentRow = feature.GetFieldAsInteger( "row" )
    	currentCol = feature.GetFieldAsInteger( "col" )
    	currentWaterDepth = feature.GetFieldAsDouble( "WaterDepth" )
    	currentStage = feature.GetFieldAsDouble( "Stage" )

	rowListPos.append( currentRow )
	colListPos.append( currentCol )

	if deBug: print "Row: %d"  % currentRow
	if deBug: print "Cow: %d"  % currentCol
	if deBug: print "Depth: %f"  % currentWaterDepth
	if deBug: print "Stage: %f"  % currentStage

	depthPos[ currentRow, currentCol ] = currentWaterDepth
	stagePos[ currentRow, currentCol ] = currentStage


for feature in layerNeg:
	currentRow = feature.GetFieldAsInteger( "row" )
    	currentCol = feature.GetFieldAsInteger( "col" )
    	currentWaterDepth = feature.GetFieldAsDouble( "WaterDepth" )
    	currentStage = feature.GetFieldAsDouble( "Stage" )

	rowListNeg.append( currentRow )
	colListNeg.append( currentCol )

	if deBug: print "Row: %d"  % currentRow
	if deBug: print "Cow: %d"  % currentCol
	if deBug: print "Depth: %f"  % currentWaterDepth
	if deBug: print "Stage: %f"  % currentStage

	depthNeg[ currentRow, currentCol ] = currentWaterDepth
	stageNeg[ currentRow, currentCol ] = currentStage

# Populate array of average stage and average depth from all the shape files
# processed
#

print "no. rows: %d" % ( len( rowListPos ) )
print "no. cols: %d" % ( len( colListPos ) )

print "no. rows: %d" % ( len( rowListNeg ) )
print "no. cols: %d" % ( len( colListNeg ) )

for i in range( 0, 46818 ):

	stageDiff[ rowListPos[ i ], colListPos[ i ] ] = ( stagePos[ rowListPos[ i ], colListPos[ i ] ] -  stageNeg[ rowListPos[ i ], colListPos[ i ] ] )
	depthDiff[ rowListPos[ i ], colListPos[ i ] ] = ( depthPos[ rowListPos[ i ], colListPos[ i ] ] -  depthNeg[ rowListPos[ i ], colListPos[ i ] ] ) 
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

outLayerName = "edenEpaDiff" 
outPathName = "/physical/gis/eden/" + outLayerName + ".shp"

# Delete shapefile if it exists
#
 
if os.path.isfile( outPathName ):

        print "File exists, must be deleted: %s" % outPathName 
        systring = "rm /physical/gis/eden/*edenEpaAvgMay*"
        if ( os.system( systring ) ) == 0:
                print "file deleted"
        else: print "could not delete file"

# Create Data Source: the directory where the shapefile goes (depends on driver)
#

if deBug: print "Creating outDataSource"
outDataSource = outDriver.CreateDataSource( "/physical/gis/eden" ) 

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

                feature.SetField( "WaterDepth", float( depthDiff[ i, j ] ) )
                feature.SetField( "Stage", float( stageDiff[ i, j ] ) )
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





