import os
import ntpath
import numpy as np
import fiona
import rasterio

data_path = '../data/1_strucdiv/'
infys_shapefile = '1.1_strucdiv_infys.shp'
train_file = '1.1_train_table.csv'

# Make a list of files with a certain ending.
# Search is recursive and traverses all (sub)folders.
def list_files(directory, endswith=".tif"):
    files_endswith = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(endswith):
                fullpath = root + '/' + file
                files_endswith.append(fullpath)
    return files_endswith

# Obtain point coordinates from a point feature in a shapefile.
def coords(point):
    x = point['geometry']['coordinates'][0]
    y = point['geometry']['coordinates'][1]

    return {'coordinates' : (x, y)}

# Obtain the data associated to a variable of a shapefile.
def values(points, variable):
    npoints = len(points)
    nvalues = np.zeros(npoints)
    i=0
    for point in points:
        val = point['properties'][variable]
        nvalues[i] = val
        i += 1
    return(nvalues)


# Given a shapefile read with fiona extract raster values.
def extract(points, raster):

    npoints = len(points)
    ex_values = np.zeros(npoints)
    i=0
    with rasterio.open(raster) as src:
        for point in points:
            for value in src.sample([coords(point)['coordinates']]):
                ex_values[i] = value
                i += 1
    return ex_values


# From a pair (spatial_sampling_points, raster_variable_list)
# Create a traininig table for model building.
# First column is considered the dependent variable.
def create_trainset(points, file_list, variable):

    trainset = np.empty((len(points), len(file_list) + 1))
    vals = values(points = points, variable = variable)
    trainset[:,0] = values(points = points, variable = variable)

    i=1
    for file in file_list: 
        trainset[:,i] = extract(points = points, raster = file)
        i += 1 

    return(trainset) 

def main():
    
    geotiffs = list_files(data_path)

    shapef = fiona.open(data_path + infys_shapefile)

    train_table = create_trainset(shapef, geotiffs, 'AlturTtl_m')

    np.savetxt(data_path + train_file, train_table, delimiter=',')

if __name__ == "__main__":
    main()