#!/usr/bin/env python3

#
# create a depth/stage shapefile for a specific day OR every day in the eden netCDF file

##import osgeo
##import osgeo.osr
##import osgeo.ogr

# if you use the sytax below, then you dont
# have to prefix all of them with osgeo
#

from osgeo import osr
from osgeo import ogr
from osgeo import gdal
import sys
import string
import os
import subprocess
import numpy
import datetime
import time
from argparse import ArgumentParser
from scipy.io import netcdf
import subprocess

def main():

    args = parseCmdLine()

    if args.verbose: print( __name__ )
    if args.verbose: print( args )

#   this is probably not need as I am not sure exactly what it does
#
    gdal.UseExceptions()

# netCDF_fileName is the quarterly netCDF file from eden
#
    surfaceDateInFile = False

# Determine if we are running all days in the netCDF File
# or just one day
#
    if args.surfaceDateString:

        allDays = False
        date_field = args.surfaceDateString.split( '-' ) 

        year = date_field[ 0 ]
        month = date_field[ 1 ]
        day = date_field[ 2 ]
        surfaceDate = datetime.date( int( year ), int( month ), int( day ) )

    else:
        surfaceDate = None
        allDays = True

    dataDir = "/physical/agency_data/eden"
    gisDir = "/physical/gis/eden"

#	lsel netcdf hardcoded b/c it rarely changes
#
    netcdf_lsel_filename = dataDir + "/dem/eden_dem_cm_oc11.nc"

#	open netCDF files
#
    if args.verbose: print ( "netcdf stage file: %s" % args.netCDF_fileName )
    stage_input = netcdf.netcdf_file( args.netCDF_fileName, 'r' )

    if args.verbose: print ( "netcdf lsel file: %s" % netcdf_lsel_filename )
    lsel_input = netcdf.netcdf_file( netcdf_lsel_filename, 'r' )

    depth = numpy.zeros( ( 405, 287 ), 'f' )

    stage = stage_input.variables[ 'stage' ][ : ]
    lsel = lsel_input.variables[ 'dem' ][ : ]
    ntime,nrowStage, ncolStage = stage.shape
    nrowLsel, ncolLsel = lsel.shape

    if nrowStage != nrowLsel or ncolStage != ncolLsel:
        print ( "Warning lsel shape and stage shape are NOT the same" )
        print ( "stage nrow: %s ncol: %s" % ( nrowStage, ncolStage ) )
        print ( " lsel nrow: %s nclo: %s" % ( nrowLsel, ncolLsel ) )

#
# Get a python date from the netCDF time attribute: time.units
#
    netCdfStageDate = stage_input.variables[ 'time' ]

    dateUnitString = netCdfStageDate.units.decode() 

    dateUnitStringField =  dateUnitString.split()

    iso_datetime = dateUnitStringField[ 2 ]

    date_time_field = str( iso_datetime).split('T')

    date_field = date_time_field[ 0 ].split( '-' )

    year = date_field[ 0 ]
    month = date_field[ 1 ]
    day = date_field[ 2 ]

    netCdfStartDate = datetime.date( int( year ), int( month ), int( day ) )

# for each day in the netCdf file...
#
    netCdfDateList = []
    for day in range( 0, ntime ):

        day_offset = datetime.timedelta( days = day )
        netCdfSurfaceDate = netCdfStartDate + day_offset

        if args.verbose: netCdfDateList.append( netCdfSurfaceDate )

# figure out if we are doing just one day or all days in the 
# netCDF file
# 
        if args.surfaceDateString: 

            if netCdfSurfaceDate != surfaceDate:
                continue
            else:
                surfaceDateInFile = True

        dateStamp = "%d%02d%02d" % ( netCdfSurfaceDate.year, netCdfSurfaceDate.month, netCdfSurfaceDate.day )
        iso_date = "%d-%02d-%02d" % ( netCdfSurfaceDate.year, netCdfSurfaceDate.month, netCdfSurfaceDate.day )

# For each column for each row
# calc depth from stage and lsel
#

        for i in range( 0, nrowStage ):
            for j in range( 0, ncolStage ):

                if numpy.isnan( lsel[ i, j ] ): 
                    continue

                depth[ i, j ] = ( stage[ day, i, j ] - lsel[ i, j ] )
#
# Create and Define the Spatial Reference

        if args.verbose: print ( "Creating Spatial Reference" ) 

        spatialReference = osr.SpatialReference() 
        spatialReference.ImportFromProj4('+proj=utm +zone=17 +ellps=WGS84 +datum=WGS84 +units=m')

#
# Establish Driver for Shapefile

        if args.verbose: print ( "creating driver" ) 

        driverName =  "ESRI Shapefile"
	
        driver = ogr.GetDriverByName( driverName )

        if driver is None:
            print ( "Driver Not Available: %s" % driverName ) 
            sys.exit( 1 )

        if args.verbose: print ( "creating dataSource" ) 

        dataSource = driver.CreateDataSource( gisDir )

        if dataSource is None:
            print  ( "Creation of DataSource output file FAILED"   ) 
            sys.exit( 1 )

        if args.verbose: print ( "creating Layer" ) 

# GIS Section
#
# Create the Layer
# This will be the name of the shapefile that is written to the DataSource Directory
#

        layer_name = "eden_epa" + dateStamp

# delete file if it exists
#
        pathFileName =  gisDir + "/" + layer_name + ".shp"

        if os.path.isfile( pathFileName ):

            print ( "File exists, must be deleted: %s" % pathFileName ) 

##            cmd = [ 'rm', pathFileName ]
##            if ( subprocess.call( cmd ) ) == 0:

            fileSpecification = gisDir + '/' + layer_name + '.*'
            systring = 'rm ' +  fileSpecification  
            if subprocess.call( systring, shell=True ) == 0:
                print ( "file deleted" ) 
            else: print ( "could not delete file" ) 

        if args.verbose: print ( "Creating: %s\n" % pathFileName ) 

        try:
            grid_layer = dataSource.CreateLayer( layer_name, spatialReference, ogr.wkbMultiPolygon )
        except NameError:
            print( 'Creations of grid_layer Failed Miserably' )
            raise

        print ( type( grid_layer )  )
        print ( "grid_layer" ) 

# Add fields to the layer
# ogr.FieldDefn return instances of the class osgeo.ogr.FieldDefn
#

        field_row = ogr.FieldDefn( "row", ogr.OFTInteger )
        field_col = ogr.FieldDefn( "col", ogr.OFTInteger )
        field_Stage = ogr.FieldDefn( "Stage", ogr.OFTReal )
        field_WaterDepth = ogr.FieldDefn( "WaterDepth", ogr.OFTReal )


# Create the fields in the layer from the FieldDefns above
#

        grid_layer.CreateField( field_row )
        grid_layer.CreateField( field_col )
        grid_layer.CreateField( field_WaterDepth )
        grid_layer.CreateField( field_Stage )

# dont think I need this. The layer is a multipolygon already
# multipolygon = ogr.Geometry( ogr.wkbMultiPolygon )

#
# get the layer def to create the features
#
        grid_layer_defn = grid_layer.GetLayerDefn()

        if args.verbose: print ( "creating Geometry" ) 

##left_edge_x = 476800
        left_edge_x = 463200
        bottom_edge_y = 2790000

        start_y = bottom_edge_y

        for i in range( 0, nrowStage ):

#	offset start_x 400m to west which is cancelled out in next loop
#
            start_x = left_edge_x - 400
            start_y = bottom_edge_y + ( i * 400 )

            for j in range( 0, ncolStage ):

                start_x += 400

                if numpy.isnan( lsel[ i, j ] ): 
                    continue

                feature = ogr.Feature( grid_layer_defn )
#
#	This code would not work until I casted the depth as float
#	But the rest of them worked fine, probably b/c they are ints
#

                feature.SetField( "WaterDepth", float( depth[ i, j ] ) ) 
                feature.SetField( "Stage", float( stage[day, i, j ] ) ) 
                feature.SetField( "row", i ) 
                feature.SetField( "col", j ) 
# 
# Fields of the feature are set individually, then destroyed
# the new one is created above with the same grid_layer_defn...
# i think?


                ring = ogr.Geometry( ogr.wkbLinearRing )

                ring.AddPoint( start_x, start_y )
                ring.AddPoint( start_x + 400, start_y )
                ring.AddPoint( start_x + 400, start_y + 400 )
                ring.AddPoint( start_x, start_y + 400 )
                ring.AddPoint( start_x, start_y )
                cell = ogr.Geometry( ogr.wkbPolygon )
                cell.AddGeometry( ring )
	
                feature.SetGeometry( cell )

## it seems that a shapefile provide this for free
##		featureIndex = ( ( i * j) + j ) 
##		feature.SetFID( featureIndex )

                grid_layer.CreateFeature( feature )
# guidance from here: https://trac.osgeo.org/gdal/wiki/PythonGotchas indicates
#    that one should basically never use destroy.  It says it is not needed at
#    all to mitigate for leaks b/c python takes care of it when it goes out of scope
#    anyway. it suggested setting it to none if you really wanted to do something useful
#    AND, serendipitously using the None made this error go away:
#
#               file exists, must be deleted: /physical/gis/eden/eden_epa20000105.shp
#               file deleted
#               ERROR 4: Unable to open /physical/gis/eden/eden_epa20000105.shp or /physical/gis/eden/eden_epa20000105.SHP.
#               ERROR 4: Failed to open file /physical/gis/eden/eden_epa20000105.shp.
#               It may be corrupt or read-only file accessed in update mode.
#
#                feature.Destroy()
                feature = None


    if allDays == False and surfaceDateInFile == False:
        sys.exit( "\nDate Entered ***** %s ***** is Not in the netCDF File\n" % surfaceDateString ) 

#    dataSource.Destroy()
    dataSource = None

    if args.verbose: print( netCdfDateList )

#-----------------------------------------------------------------------------------------------------------
#  Parse Command Line Args

def parseCmdLine():

    home_dir = os.getenv( 'HOME', default = os.getcwd() )

    parser = ArgumentParser( description = "Eden netCDF to Shapefile" )

    parser.add_argument( 'netCDF_fileName',
                        type = str,
                        action = 'store',
                        help = 'netCDF File Name' )

    parser.add_argument( '-d', '--date',
                        dest = 'surfaceDateString',
                        type = str,
                        action = 'store', 
                        help = 'date yyyy-mm-dd for shapefile output' )

    parser.add_argument( '-v', '--verbose',
                        action = 'store_true',
                        help = 'to provide additional output' )

    args = parser.parse_args()
    return args

#----------------------------------------------------------------------------
# Provide for cmd line invocation: not executed on import

if __name__ == '__main__' :
    main()
