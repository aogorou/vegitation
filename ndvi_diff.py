import ee
import colorcet as cc
import folium

ee.Authenticate()
ee.Initialize()


def add_ee_layer(self, ee_image_object, vis_params, name):
  map_id_dict = ee.Image(ee_image_object).getMapId(vis_params)
  folium.raster_layers.TileLayer(
      tiles=map_id_dict['tile_fetcher'].url_format,
      attr='Map Data &copy; <a href="https://earthengine.google.com/">Google Earth Engine</a>',
      name=name,
      overlay=True,
      control=True
  ).add_to(self)

def maskS2clouds(image):
    qa = image.select('QA60')

  # Bits 10 and 11 are clouds and cirrus, respectively.
    cloudBitMask = 1 << 10
    cirrusBitMask = 1 << 11

    # Both flags should be set to zero, indicating clear conditions.
    mask = qa.bitwiseAnd(cloudBitMask).eq(0) and qa.bitwiseAnd(cirrusBitMask).eq(0)

    return image.updateMask(mask).divide(10000)

folium.Map.add_ee_layer = add_ee_layer

imageCollection = ee.ImageCollection('COPERNICUS/S2_SR')

before = imageCollection.filterDate('2020-12-31','2021-02-28').filter(\
         ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE',20)).map(maskS2clouds)
after = imageCollection.filterDate('2021-07-01','2021-09-30').filter(\
        ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE',20)).map(maskS2clouds)
        
waterOcc = ee.Image("JRC/GSW1_0/GlobalSurfaceWater").select('occurrence')
jrc_data0 = ee.Image("JRC/GSW1_0/Metadata").select('total_obs').lte(0)
waterOccFilled = waterOcc.unmask(0).max(jrc_data0)
waterMask = waterOccFilled.lt(50)

def calc_ndvi(image):
    return ee.Image(image.expression(
    '(NIR-RED)/(NIR+RED)', {
      'RED': image.select('B4'),
      'NIR': image.select('B8')
}))

ndvi_before = before.map(calc_ndvi)
ndvi_before_mean = ndvi_before.mean()
ndvi_after = after.map(calc_ndvi)
ndvi_after_mean = ndvi_after.mean()
ndvi = ndvi_after_mean.subtract(ndvi_before_mean)

lat, lon = 34.953140, 137.169711
visualization = {
  'min': 0.0,
  'max': 1.0,
  'palette': cc.fire
}
my_map = folium.Map(location=[lat, lon], zoom_start=10)
my_map.add_ee_layer(ndvi_before_mean, visualization, '')
#my_map.add_ee_layer(ndvi.updateMask(waterMask), visualization, '')

display(my_map)
my_map.save('/content/drive/My Drive/GEE_NDVI/NDVI_2020winter.html')

my_map = folium.Map(location=[lat, lon], zoom_start=10)
my_map.add_ee_layer(ndvi_after_mean, visualization, '')
display(my_map)
my_map.save('/content/drive/My Drive/GEE_NDVI/NDVI_2021summer.html')

my_map = folium.Map(location=[lat, lon], zoom_start=10)
my_map.add_ee_layer(ndvi, visualization, '')
display(my_map)
my_map.save('/content/drive/My Drive/GEE_NDVI/NDVI_diff.html')


visualization = {
    'min': 0.0,
    'max': 0.3,
    'bands': ['B4', 'B3', 'B2']
}

my_map = folium.Map(location=[lat, lon], zoom_start=10)
my_map.add_ee_layer(after.mean(), visualization, '')

display(my_map)
my_map.save('/content/drive/My Drive/GEE_NDVI/NDVI_RGB.html')
