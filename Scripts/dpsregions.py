import folium
from folium.features import DivIcon
import pandas as pd
import geopandas as gpd
import fiona
from folium.features import DivIcon
from branca.utilities import split_six

# DPS Regions dictionary. Values copied and pasted from the bottom portion of each region's public facing web page on https://www.dps.texas.gov/
dpsregions = {
    "DPS Region 1":'Anderson, Bowie, Camp, Cass, Cherokee, Collin, Cooke, Dallas, Delta, Denton, Ellis, Erath, Fannin, Franklin, Grayson, Gregg, Harrison, Henderson, Hood, Hopkins, Hunt, Johnson, Kaufman, Lamar, Marion, Morris, Panola, Navarro, Palo Pinto, Parker, Rains, Red River, Rockwall, Rusk, Smith, Somervell, Tarrant, Titus, Upshur, Van Zandt, Wise, Wood',
    "DPS Region 2":'Angelina, Austin, Brazoria, Brazos, Burleson, Chambers, Colorado, Fort Bend, Galveston, Grimes, Hardin, Harris, Houston, Jasper, Jefferson, Leon, Liberty, Madison, Matagorda, Montgomery, Nacogdoches, Newton, Orange, Polk, Robertson, Sabine, San Augustine, San Jacinto, Shelby, Trinity, Tyler, Walker, Waller, Washington, Wharton',
    "DPS Region 3":'Aransas, Bee, Brooks, Cameron, Dimmit, Duval, Edwards, Hidalgo, Jim Hogg, Jim Wells, Kenedy, Kinney, Kleberg, LaSalle, Live Oak, Maverick, Nueces, Real, Refugio, San Patricio, Starr, Webb, Willacy, Uvalde, Val Verde, Zapata, Zavala',
    "DPS Region 4":'Andrews, Borden, Brewster, Coke, Concho, Crane, Crockett, Culberson, Dawson, Ector, El Paso, Gaines, Glasscock, Howard, Hudspeth, Irion, Jeff Davis, Kimble, Loving, Mason, Martin, McCulloch, Menard, Midland, Pecos, Presidio, Reagan, Reeves, Schleicher, Sterling, Sutton, Terrell, Tom Green, Upton, Ward, Winkler',
    "DPS Region 5":'Archer, Armstrong, Bailey, Baylor, Briscoe, Brown, Callahan, Carson, Castro, Clay, Childress, Cochran, Coleman, Collingsworth, Comanche, Cottle, Crosby, Dallam, Deaf Smith, Dickens, Donley, Eastland, Fisher, Floyd, Foard, Garza, Gray, Hale, Hall, Hansford, Hardeman, Hartley, Haskell, Hemphill, Hockley, Hutchinson, Jack, Jones, Kent, King, Knox, Lamb, Lipscomb, Lubbock, Lynn, Mitchell, Montague, Moore, Motley, Nolan, Ochiltree, Oldham, Parmer, Potter, Randall, Roberts, Runnels, Scurry, Shackleford, Sherman, Stephens, Stonewall, Swisher, Taylor, Terry, Throckmorton, Wheeler, Wichita, Wilbarger, Yoakum, Young',
    "DPS Region 6":'Atascosa, Bandera, Bastrop, Bell, Bexar, Blanco, Bosque, Burnet, Caldwell, Calhoun, Comal, Coryell, DeWitt, Falls, Fayette, Freestone, Frio, Gillespie, Goliad, Gonzales, Guadalupe, Hamilton, Hays, Hill, Jackson, Karnes, Kendall, Kerr, Lampasas, Lavaca, Lee, Limestone, Llano, McMullen, Medina, Milam, Mills, McLennan, San Saba, Travis, Victoria, Williamson, Wilson',
}

# Converting the long strings to a list
for region in dpsregions:
    dpsregions[region]=dpsregions[region].split(', ')

# Building a list of lists assigning the DPS Region into a list with each county that is listed under it.
for region in dpsregions:
    dpsregions[region]=[[region, county] for county in dpsregions[region]]

# Flattened list object to feed into a Dataframe
dps_regions_list = [item for key in dpsregions for item in dpsregions[key]]

# Reading in some census data
census_data = pd.read_excel('../data/Dtl2010hcat.xls')

# Cleaning up the data (syntax)
census_data = census_data[['Area','Total']].loc[(census_data['AgeGroup'] == "'ALL'") & (census_data['Area'] != 'Texas')]
census_data=census_data.rename(columns={'Area':'NAME', 'Total':'Total Population'})
census_data['NAME'].loc[census_data['NAME'] == 'DE WITT'] = 'DEWITT'
census_data['NAME'] = census_data['NAME'].str.upper()

# Reading in a county shapefile layer, cutting it down, and cleaning it up.
counties = gpd.read_file('../tl_2011_us_county/tl_2011_us_county.shp')
counties = counties.loc[counties['STATEFP']=='48']
counties['NAME'] = counties['NAME'].str.upper()

# More cleaning ( spelling ;-) ) and syntax.
dps_regions_list = gpd.GeoDataFrame(dps_regions_list, columns=['DPSRegion', 'NAME'])
dps_regions_list['NAME'].loc[dps_regions_list['NAME'] == 'Shackleford'] = 'Shackelford'
dps_regions_list['NAME'].loc[dps_regions_list['NAME'] == 'LaSalle'] = 'La Salle'
dps_regions_list['NAME'] = dps_regions_list['NAME'].str.upper()

# Dissolving the county polygons into larger Metro regions.
stats_areas = counties.dissolve(by='CBSAFP', as_index=False)

# Merging the county data with census data (Population)
counties = counties.merge(census_data, on='NAME')
counties = counties.merge(dps_regions_list, on='NAME', )
counties = gpd.GeoDataFrame(counties).sort_values(by='Total Population', ascending=False)

# Dissolving the county polygons into larger Metro regions.
CBSAFP = counties.dissolve(by='CBSAFP', as_index=False, aggfunc='sum')

# Dissolving the county polygons into DPS regions.
regions = counties.dissolve(by='DPSRegion',as_index=False, aggfunc='sum')

# Instantiating the folium Map object
regionsmap = folium.Map([31.2338,-98.6768], tiles='OpenStreetMap', zoom_start=6)

# Assigning a threshold scale based on Population
thresholdscale = split_six(regions['Total Population'])

# Adding a choropleth map of the DPS regions as the first layer.
regionsmap.choropleth(
    geo_data=regions.to_json(), data=regions, name='Texas DPS Region Polygons',columns=['DPSRegion','Total Population'],
    legend_name= 'Texas DPS Regions by Population',key_on='feature.properties.DPSRegion', threshold_scale=thresholdscale,
    fill_color='OrRd', fill_opacity=0.5, highlight=True, line_weight=3.0,
)

# A MSA dictonary to reverence the CBSAFP codes to
msa_dict = {
    "12420":"Austin-Round Rock-San Marcos, TX Metro Area",
    "41700":"San Antonio-New Braunfels, TX Metro Area",
    "26420":"Houston-Sugar Land-Baytown, TX Metro Area",
    "19100":"Dallas-Fort Worth-Arlington, TX Metro Area"
}

# A function to query the county names that fall within a region.
def get_counties_from_field(value, field):
    return ', '.join([county for county in counties['NAMELSAD'].loc[counties[field]==value]])

# A feature group for the markers with the population information for DPS regions
fg = folium.FeatureGroup(name="Texas DPS Region Population Details")
fg.layer_name = 'Texas DPS Region Population Details'
for name, geo, pop in zip(regions['DPSRegion'],regions.geometry, regions['Total Population']):
    folium.map.Marker([geo.centroid.y, geo.centroid.x],
                      popup=f"{'<br>'.join(['<b>Texas '+name+'</b>', 'Total Population: '+'''{:3,.0f}'''.format(pop)])}" + '<br>' +
                            f"Includes the following Counties, highest to lowest population:<br>{get_counties_from_field(name, 'DPSRegion')}",
                      icon=DivIcon(icon_size=(50,150), icon_anchor=(30,0), popup_anchor=(50,0), html=f'<div style="font-size:14pt; font-family:helvetica neue; text-align:center"><b>{name}</b></div>'),
                      ).add_to(fg)

# Another feature group for the major MSAs
pop_centers = folium.FeatureGroup(name='Texas Population Centers')

# Prepping the geodataframe for projection
CBSAFP.crs = fiona.crs.from_epsg(4326)
CBSAFP = CBSAFP.sort_values(by="Total Population", ascending=False).iloc[:4]

# Simplifying the polygon's edges to give us a more uniform feature on the map.
CBSAFP.geometry = CBSAFP['geometry'].apply(lambda feature: feature.simplify(0.2, preserve_topology=False))

# Instantiating the GEOJSON object to feed to the map
folium.GeoJson(CBSAFP,
    highlight_function=lambda feature: {'weight': 3,
                                          'fillOpacity': 0.2,
                                          'fillColor':'#4947FF',
                                          'color':"#5D0C0E",
                                          'borderOpacity': 0.0,
                                          },
    # STYLE
    style_function=lambda feature:{'weight': 2,
                                          'fillOpacity': 0.1,
                                          'fillColor':'#4947FF',
                                          'color':"#423e41",
                                          'borderOpacity': 0.0,
                                          },
    smooth_factor=2.0).add_to(pop_centers)

# Detail point layer for the MSAs
for geo, cbs, pop in zip(CBSAFP.geometry, CBSAFP.CBSAFP, CBSAFP['Total Population']):
    folium.Marker([geo.centroid.y, geo.centroid.x], icon=folium.Icon(color='black', icon_color='white'),
                  popup=f"{'<br>'.join([msa_dict[str(cbs)], 'Total Population: ''''{:3,.0f}'''.format(pop)])}"+'<br>'+
                        f"Includes the following Counties, highest to lowest population:<br>{get_counties_from_field(cbs, 'CBSAFP')}"
                  ).add_to(pop_centers)

# adding the feature groups to the map.

fg.add_to(regionsmap)
pop_centers.add_to(regionsmap)

# Adding layer control to the map
folium.LayerControl().add_to(regionsmap)

# Saving the map to an HTML file.
regionsmap.save('TexasDPSRegions.html')
