import numpy as np
import gc
from osgeo import gdal
from osgeo.gdalconst import GA_ReadOnly 
from osgeo.gdalconst import GDT_Float32
from osgeo.gdalconst import GDT_Int16

data_path = '../data/2_landcover/'
in_raster = 'madmex_lcc_landsat_2018_v4.3.1_chp_7c.tif'
out_raster = 'madmex_lcc_landsat_2018_v4.3.1_chp_7cprop.tif'

def multispectralToBits(multispec_raster_path,class_ids):
	# Get data from raster with classifications
	ds = gdal.Open(multispec_raster_path)
	band = ds.GetRasterBand(1)
	class_ar = band.ReadAsArray()
	gt = ds.GetGeoTransform()
	pj = ds.GetProjection()
	ds = band = None  # close

	# Make a new bit rasters
	drv = gdal.GetDriverByName('GTiff')
	ds = drv.Create('bit_raster.tif', class_ar.shape[1], class_ar.shape[0],
		len(class_ids), gdal.GDT_Byte, ['NBITS=1'])
	ds.SetGeoTransform(gt)
	ds.SetProjection(pj)
	for bidx in range(ds.RasterCount):
		band = ds.GetRasterBand(bidx + 1)
		# create boolean result where 0 == no and 1 == yes
		selection = (class_ar == class_ids[bidx]).astype("u1")
		band.WriteArray(selection)
	ds = band = None  # save, close

def main():
	
	# Open raster.
	class_ids=[1,2,4,5,6,7]
	multispectralToBits(data_path + in_raster, class_ids)

	src_ds = gdal.Open('bit_raster.tif')

	# Open a template or copy array, for dimensions and NODATA mask.
	cpy_ds = gdal.Open(data_path + '1.2_avg_tree_height.tif')
	band = cpy_ds.GetRasterBand(1)
	cpy_mask = (band.ReadAsArray() == band.GetNoDataValue())
	
	# Result raster, with same resolution and position as the copy raster.
	drv = gdal.GetDriverByName('GTiff')
	dst_ds = drv.Create(data_path + out_raster, cpy_ds.RasterXSize, cpy_ds.RasterYSize,
	                    len(class_ids), gdal.GDT_Float32, ['INTERLEAVE=BAND'])
	dst_ds.SetGeoTransform(cpy_ds.GetGeoTransform())
	dst_ds.SetProjection(cpy_ds.GetProjection())

	# Do the same as gdalwarp -r average; this might take a while to finish.
	gdal.ReprojectImage(src_ds, dst_ds, None, None, gdal.GRA_Average)

	# Convert all fractions to percent, and apply the same NODATA mask from the copy raster.
	NODATA = 0
	for bidx in range(dst_ds.RasterCount):
	    band = dst_ds.GetRasterBand(bidx + 1)
	    ar = band.ReadAsArray() * 100.0
	    ar[cpy_mask] = NODATA
	    band.WriteArray(ar)
	    band.SetNoDataValue(NODATA)

	# Save and close all rasters
	src_ds = cpy_ds = dst_ds = band = None

if __name__ == "__main__":
    main()