import math
import os
import ntpath
import rasterio
import numpy as np
from sklearn.ensemble import RandomForestRegressor


data_path = "../data/1_strucdiv/"
train_file = "1.1_train_table.csv"

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

# Get raster dimensions.
def dims(raster):
    with rasterio.open(raster, 'r') as ds:
        raster = ds.read()

    raster_dimensions = raster.shape    
    x = raster_dimensions[1]
    y = raster_dimensions[2]
    return (x,y)

# Given a raster file-list create a numpy array.
# Each raster (variable) becomes a column.
def rasters_to_table(file_list):

    # Read in first raster to extract metadata.
    xy = dims(file_list[0])
 
    x = xy[0]
    y = xy[1]

    # Initialize numpy array to place raster bands.
    ntable = np.zeros((x*y, len(file_list)))
    i = 0
    for raster in file_list:
        with rasterio.open(raster, 'r') as ds:
            ntable[:,i] = ds.read().flatten()
            i += 1

    return(ntable)

def main():
    # Load training data array.
    data = np.loadtxt(data_path + train_file, delimiter=',')

    # Instantiate model with 1000 decision trees.
    # n_jobs is subject to available cores (8 cores in parallel in this case).
    model = RandomForestRegressor(n_estimators = 100, random_state = 42, oob_score = True, n_jobs = 8)

    # Train the model.
    model.fit(data[:,1:], data[:,0])

    # Out-Of-Bag estimation of correlatino between observed and predicted values.
    oob_corr = math.sqrt(model.oob_score_)
    print(oob_corr)

    # Use the forest's predict method on the full data set (all of MX).
    geotiffs = list_files(data_path)

    rast = rasterio.open(geotiffs[0])

    rmetadata = rast.meta

    full_data = rasters_to_table(geotiffs)
    predictions = model.predict(full_data).astype('float32')
    predictions = predictions.reshape((rmetadata['height'], rmetadata['width']))

    with rasterio.open(data_path + "1.2_avg_tree_height.tif", 'w', **rmetadata) as dst:
    	dst.write(predictions, indexes = 1)


if __name__ == "__main__":
    main()

