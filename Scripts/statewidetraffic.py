import geopandas as gpd
import pandas as pd
import folium
from branca.utilities import split_six


# Reading in a Shapefile that contains all the TXDOT traffic reporting data.
pcs = gpd.read_file('TxDOT_AADT/TxDOT_AADT.shp')

# Instantiating a list to append to
cnty_daily_traf_totals = []

for x in pcs['T_CNTY_NM'].unique():
    instance = pcs[['F2015_TRAF','T_CNTY_NM']].loc[pcs['T_CNTY_NM'] == x]
    cnty_daily_traf_totals.append([x,sum(instance['F2015_TRAF'])])

# Reading in Census population data for each Texas County to a pandas Dataframe.
census_data = pd.read_excel('Dtl2010hcat.xls')

census_data = census_data[['Area','Total']].loc[(census_data['AgeGroup'] == "'ALL'") & (census_data['Area'] != 'Texas')].sort_values(by='Total', ascending=False)
census_data=census_data.rename(columns={'Area':'CountyName', 'Total':'Total Population'})

# 'DEWITT' was spelled with a space in our original
census_data['CountyName'].loc[census_data['CountyName'] == 'DE WITT'] = 'DEWITT'

# Creating a GeoDataframe for the list we built earlier, with the sum of the traffic totals.
gdf = gpd.GeoDataFrame(cnty_daily_traf_totals, columns=['CountyName','2015Traffic'])
gdf['CountyName'] = gdf['CountyName'].apply(lambda x: x.upper())

# Reading in a United States county shapefile.
county_shp = gpd.read_file('tl_2011_us_county/tl_2011_us_county.shp')
# Winnowing our County Spatial data to Texas Counties only (based on state FIPS code)
county_shp = county_shp.loc[county_shp['STATEFP']=='48']
county_shp = county_shp.rename(columns={'NAME':'CountyName'})
county_shp['CountyName'] = county_shp['CountyName'].apply(lambda x: x.upper())

census_data = gpd.GeoDataFrame(census_data)
census_data['CountyName'].apply(lambda x: x.upper())
gdf = gdf.merge(census_data, on='CountyName')
gdf = gdf.merge(county_shp, on='CountyName')
gdf['TrafficperCapita'] = gdf['2015Traffic'] / gdf['Total Population']
gdf = gpd.GeoDataFrame(gdf)

gdf = gdf.sort_values(by='TrafficperCapita', ascending=False)
gdf.geometry = gdf['geometry']
m = folium.Map([31.2338,-98.6768], tiles='Stamen Toner', zoom_start=6)

thresholdscale = split_six(gdf['TrafficperCapita'])

m.choropleth(geo_data=gdf.to_json(), data=gdf, columns=['CountyName','TrafficperCapita'], name='Road Traffic Counts in Texas Counties, per Capita 2015', legend_name='Average Daily Traffic Count per Capita',
             key_on='feature.properties.CountyName', fill_color='OrRd', fill_opacity=0.9, threshold_scale=thresholdscale,
             highlight=True,
             )

datadict = {'2015 Traffic County Details':gdf}

def addlayer(dictobject):
    for geodata in dictobject:
        fg = folium.FeatureGroup(name=geodata)
        local = dictobject[geodata]
        for geo, traffic15, totPop, trafCapita, countyname in zip(local.geometry, local['2015Traffic'], local['Total Population'], local['TrafficperCapita'], local['NAMELSAD']):
            folium.Marker([geo.centroid.y, geo.centroid.x], icon=folium.Icon(prefix='fa', icon='info-circle', color='black'),
                          popup=f"{'<br>'.join([countyname, 'Average Daily Traffic: '+'''{:3,.0f}'''.format(traffic15),'Total Population: '+'''{:3,.0f}'''.format(totPop), 'Traffic per Capita: '+'''%3.0f'''%trafCapita])}"
                          ).add_to(fg)
        fg.add_to(m)

addlayer(datadict)

folium.LayerControl().add_to(m)
m.save('trafficdata.html')