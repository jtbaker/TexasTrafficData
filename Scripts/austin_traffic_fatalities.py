import pandas as pd
import fiona
import geopandas as gpd
import folium
from folium import GeoJson
from shapely.geometry import Point

# Reading our Fatality Data csv's from the Austin Open Data Portal into some pandas Dataframes.
f_2015 = pd.read_csv('../data/2015_APD_Traffic_Fatalities.csv')
f_2016 = pd.read_csv('../data/2016_APD_Traffic_Fatalities.csv')

# Getting Austin local zip codes, to winnow down our Census Tract data on later by running a spatial join.
zippath='../data/zipcodes/geo_export_f636f682-5b8a-41eb-9ec4-cfb9f60bfdf2.shp'
zips = gpd.GeoDataFrame.from_file(zippath)
zips.geometry = zips['geometry']
zips = zips.loc[zips['name'].isin(['TRAVIS','AUSTIN','PFLUGERVILLE','DEL VALLE',
                                   'MANOR','MANCHACA','LEANDER', 'CEDAR PARK'])]
# Setting coordinate system
zips.crs = fiona.crs.from_epsg(4326)

# Opening the Texas census tract layer from the directory the zip file created.
census_tracts = gpd.read_file('../data/tl_2017_48_tract/tl_2017_48_tract.shp')
census_tracts.crs = fiona.crs.from_epsg(4326)
# Spatial Join to access only the local census tracts.
census_tracts = gpd.tools.sjoin(zips, census_tracts, how='left', op='within')

gdf1 = gpd.GeoDataFrame(f_2015)
gdf2 = gpd.GeoDataFrame(f_2016)
# Cleansing the data so we have the same key values to work with.
gdf2 = gdf2.rename({'Ran Red Light or Stop Sign':'Ran Red Light','charge_slater': 'charge','restraint / helmet':'restraint'},axis='columns')

# Appending our initial dataframe to the 2nd one, after matching the key values to each other.
gdf = gdf2.append(gdf1)
# Time conversion..
# gdf['datetime'] = pd.to_datetime(gdf['Time'])
# Adding our values to a

gdf['X COORD'], gdf['Y COORD'] = pd.to_numeric(gdf['X COORD']), pd.to_numeric(gdf['Y COORD'])
geometry = [Point(xy) for xy in zip(gdf['X COORD'], gdf['Y COORD'])]
# Setting geometry
gdf['geometry'] = geometry
gdf.crs = fiona.crs.from_epsg(4326)

# Adding a pandas timestamped field for easy searchability
gdf['datetime'] = pd.to_datetime(gdf['Date']+' '+gdf['Time'])


Incidents2016 = gdf.loc[gdf['datetime']>='2016-01-01']
Incidents2015 = gdf.loc[gdf['datetime']<='2015-12-31']
Assaults = gdf.loc[(gdf['charge'].str.contains('agg', case=False, na=False)) | (gdf['charge'].str.contains('manslaughter',case=False, na=False)) | (gdf['charge'].str.contains('homicide', case=False, na=False))]
No_Seatbelts = gdf.loc[gdf['restraint'].str.contains('no seatbelt', case=False, na = False)]
Invalid_DL = gdf.loc[gdf['DL Status'] != 'ok']
Ran_Red = gdf.loc[gdf['Ran Red Light'] == 'Y']
Speeding = gdf.loc[gdf['Speeding'] == 'Y']
Daytime = gdf.loc[(gdf.Hour >= 6) & (gdf.Hour <= 7)]
Nighttime = gdf.loc[(gdf.Hour < 6) | (gdf.Hour > 7)]

sub_cats = {'2015 Incidents':{'data':Incidents2015, 'color':'blue'},
            '2016 Incidents':{'data':Incidents2016, 'color':'red'},
            'Assaults':{'data':Assaults,'color':'red'},
            'No Seatbelts':{'data': No_Seatbelts,'color':'red'},
            'Invalid DL':{'data':Invalid_DL,'color':'blue'},
            "Ran Red Light":{'data':Ran_Red,'color':'red'},
            "Speeding":{'data':Speeding,'color':'orange'},
            'Daytime':{'data': Daytime,'color': 'orange'},
            'Nighttime':{'data':Nighttime,'color':'black'}}

# Making copies of our census tract geodataframe.
fts15, fts16 = census_tracts.copy(), census_tracts.copy()
# Adding the number of points in each census tract polygon, using GeoPandas.GeoSeries.contains method. If a point
# falls on the boundary of a census tract polygon(as wanton on roadway data), it will get counted as a point for both
# census tract polygons.
fts15['NUMPOINTS'] = fts15['geometry'].apply(lambda x: len([x.contains(point) for point in tuple(Incidents2015.geometry) if x.contains(point) is True]))
fts16['NUMPOINTS'] = fts16['geometry'].apply(lambda x: len([x.contains(point) for point in tuple(Incidents2016.geometry) if x.contains(point) is True]))
census_tracts['NUMPOINTS'], census_tracts['delta'] = sum([fts15['NUMPOINTS'], fts16['NUMPOINTS']]), fts16['NUMPOINTS'] - fts15['NUMPOINTS']


# Structuring our polygon geodataframes  into a dictionary.
ctracts={'2015 Traffic Fatalities by Census Tract':fts15,'2016 Traffic Fatalities by Census Tract':fts16}
deltas = {'2015-2016 Traffic Fatality changes':census_tracts}

# Instantiating a folium Map object with our initial extent values, and the basemap we'll be using.
map = folium.Map(location=[30.2747,-97.7407], tiles='Stamen Toner', zoom_start=11,)

# Color pallette dictionary with RGB values to assign colors, based on quantity.
color_dict = {'0':'#00000000','1':'#EBB5B9','2':'#EB8A8A','3':"#EB5E5C",'4':'#EB3735','5':'#EB1F1C','6':"#EA0707",
              '7':'#BE003A','8':"#AA0034",'9':"#810029",'10':"#55001D",'11':"#55001D",'12':"#55001D",'13':"#55001D",
              '14':"#55001D"}

# Writing a function to add GeoDataFrames to the map object. Passes a dictionary object, which stores the data behind a
# string value, which will prove useful. Builds a folium FeatureGroup for each geodataframe, zips the values we specify
# into a tuple we can iterate on, and plot the values on the Map.
def add_layers(dictobject):
    for geodataframe in dictobject:
        local=dictobject[geodataframe]
        fg = folium.FeatureGroup(name=geodataframe)
        fg.layer_name = geodataframe
        try:
            data = local['data']
            for x,y,charge,time,date in zip(data['X COORD'], data['Y COORD'], data['charge'], data['Time'], data['Date']):
                folium.Marker([y,x], popup=f"Category: {geodataframe}<br>Charge: {charge}<br>Date: {pd.to_datetime(date).strftime('''%b %d, %Y''')}"+'<br>'+'Time: '+time, icon=folium.Icon(color=local['color'])).add_to(fg)
        # Handling non-point objects(our census tract polygon layers), and adding them to the feature group (fg).
        except KeyError:
            GeoJson(local,
                    highlight_function=lambda feature: {'weight': 3,
                                                          'fillOpacity': 0.8,
                                                          'fillColor':color_dict[str(feature['properties']['NUMPOINTS'])],
                                                          'color':"#5D0C0E",
                                                          'borderOpacity': 0.0,
                                                          },
                    style_function=lambda feature:{'weight': 2,
                                                          'fillOpacity': 0.6,
                                                          'fillColor':color_dict[str(feature['properties']['NUMPOINTS'])],
                                                          'color':"#423e41",
                                                          'borderOpacity': 0.0,
                                                          },
                    smooth_factor=2.0,
            ).add_to(fg)
            # adding a popup to show the details of each tract.
            for geo, pts in zip(local.geometry, local['NUMPOINTS']):
                # Adding a marker with the details for each polygon.
                folium.Marker([geo.centroid.y, geo.centroid.x],
                              popup=f"{pts} {'fatalities' if pts != 1 else 'fatality'} in this tract during {geodataframe[:4]}",
                              icon=folium.Icon(icon='bookmark', color='darkblue')
                ).add_to(fg)
        map.add_child(fg, name=geodataframe)


add_layers(ctracts)
add_layers(sub_cats)
folium.LayerControl(autoZIndex=True).add_to(map)
map.save('../sites/austinfatalities.html')