<h2>Texas Traffic Data</h2>
<br>

<p>This repository contains a series of useful scripts to automate the generation of maps for a range of datasets 
relating to auto usage and statistics in Texas. The code is annotated with comments at each step to make clear what
is happening, and some of the logic behind it.</p>

<br>

<h4>Austin Traffic Data</h4>

<p><code>austin_traffic_fatalities.py</code> generates a map that plots the locations of all traffic fatality incidents
in the City of Austin's jurisdiction (as reported by APD). It has several toggleable layers based on some of 
the classifcations in the dataset (Daytime/Nighttime, if Seatbelts were not worn, if the driver ran a red light, etc.
Information about the incident can be viewed by clicking on the marker denoting its location, which will yield a popup
with details on the incident (date, time of day, charges (if they were filed as part of the incident)).</p>

<p>It also performs a spatial join on the number of incidents within each census tract in the area, and produces a graduated
color map, based on the number of points within each tract.
</p>
<br>
<p>This map can be viewed at <a href='http://jtbaker.me/austinfatalities.html'>http://jtbaker.me/austinfatalities.html</a></p>
<br>

<h4>DPS Regions</h4>

<p><code>dpsregions.py</code> gets the counties contained within each region from the website, and merges them into a common
dataframe with a Census CSV, and County Shapefile that has other useful statistical information and geographic geometry for
each object. From this object we can perform dissovles on both the County CBSAFP (metro area) code, and the Texas DPS Region
to visualize the extent of the boundaries of these areas, and understand the population data contained within each one.
The population of each DPS Region is rendered with a graduated color map, and details can be viewed by clicking on the 
popup markers.</p> 
<br>
<p>This map can be viewed at <a href='http://jtbaker.me/DPSRegions.html'>http://jtbaker.me/DPSRegions.html</a></p>
<br>
<h4>Statewide Traffic</h4>
<p><code>statewidetraffic.py</code> ingests the same county census dataset, merges it with both the county shapefile layer,
and traffic data as collected by TXDOT. Produces a graduated color map that yields a graduated color map weighted by total traffic
count, normalized by population per capita in each county. The details can be viewed by clicking on the popup marker placed in 
the centroid of each county.<p>
<br>
<p>This map can be viewed at <a href='http://jtbaker.me/trafficdata.html'>http://jtbaker.me/trafficdata.html</a></p>
