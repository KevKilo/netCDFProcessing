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
