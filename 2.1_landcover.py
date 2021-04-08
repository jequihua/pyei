import numpy as np
import gc
from geotiffio import readtif
from geotiffio import createtif
from geotiffio import writetif
from osgeo import gdal
from osgeo.gdalconst import GA_ReadOnly 
from osgeo.gdalconst import GDT_Float32
from osgeo.gdalconst import GDT_Int16

gdal.UseExceptions()

data_path = '../data/2_landcover/'
in_raster = 'madmex_lcc_landsat_2018_v4.3.1_chp.tif'
out_raster = 'madmex_lcc_landsat_2018_v4.3.1_chp_7c.tif'

def swapValues(flattenedNumpyArray,listOfInLists,listOfSwappingValues):
	'''
	takes each list in tlistOfInLists and swaps it by the
	corresponding value in listOfSwappingValues
	'''
	aux=flattenedNumpyArray
	if len(listOfInLists)!=len(listOfSwappingValues):
		print("Lists must be of the same length.")
	else:
		for i in range(len(listOfInLists)):
			# list to numpy array
			nparray = np.array(listOfInLists[i])
			found_idx = np.in1d(flattenedNumpyArray,nparray)
			aux[found_idx]=listOfSwappingValues[i]
	aux = aux.astype(int)
	return(aux)


def main():
	
	dataset,rows,cols,bands = readtif(data_path + in_raster)

	# Image metadata.
	projection = dataset.GetProjection()
	transform = dataset.GetGeoTransform()
	driver = dataset.GetDriver()
					
	# make numpy array and flatten
	band = dataset.GetRasterBand(1)
	band = band.ReadAsArray(0, 0, cols, rows).astype(np.int16)
	band = np.ravel(band)

	# Remove missing values from class remapping.
	gooddata_idx = band != 0
	gooddata = band[gooddata_idx]

	# Raster with remapped classes.
	aggregated = swapValues(gooddata,[\
		                           [1,2,3,6],\
		                           [7,8, 9,10,11,12, 21, 22, 25, 26],\
		                           #[4,5, 13, 14, 15, 16, 17, 18, 19, 20],\
		                           [27, 28],\
		                           [23, 24, 30],\
		                           [29],\
		                           [31]
		                          ],\
								[1,2,4,5,6,7])

	# [1,2,3,8] 						  -to- 1 bosque
	# [9,10,11,12,13,14,15,16]    		  -to- 2 selvas
	# [4,5,6,7,17,18,19,21,22,23, 25, 26] -to- 3 matorrales
	# [27, 28] 							  -to- 4 pastizal y agricultura 
	# [30, 20, 24]  					  -to- 5 suelo desnudo
	# [31]      						  -to- 6 asentamiento humano
	# [29]      						  -to- 7 agua
	# [98, 99]  						  -to- 8 nieve y hielo

	band[gooddata_idx] = aggregated

	# Set up output and write.
	outData = createtif(driver, rows, cols, 1, data_path + out_raster,16)
	writetif(outData,band, projection, transform)

	# Close dataset properly.
	outData = None

if __name__ == "__main__":
    main()