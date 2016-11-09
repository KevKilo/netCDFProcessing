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
shapeFileDir = "/physical/gis/eden/recovery/"

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

for i in range( 0, day ):
    print "%6.2f" %  depth[ i, 217, 195] 


