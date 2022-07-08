""" bike_new_ka.py 
Demo-Application
Load geojson with karlsruhe bikelanes since 1980 
Create summary image and video of evolution
"""

import geopandas as gp
import datetime as dt
# matplotlib only for interactive plot
# savefig doesn't need it
import matplotlib.pyplot as plt
import matplotlib.colors as cls
import sys

# https://matplotlib.org/stable/api/animation_api.html
from matplotlib.animation import FuncAnimation

# https://geopandas.org/en/stable/gallery/plotting_basemap_background.html
import contextily as cx
# loading a basemap needs internet. Option to don't
loadMap = True

# german floats
from babel.numbers import format_decimal


df = gp.read_file("bike_new_ka.geojson")
print("CRS:",df.crs)
print("Items read:", len(df))


# we have a number of duplicate geometries. keep latest only 
df.drop_duplicates(subset = "geometry", keep="last", inplace=True)
print("Items remaining:", len(df))


print("Europe is 3035, see https://epsg.io/3035")

edf = df.to_crs("EPSG:3035")
print("New CRS:",edf.crs)

print("Lengths:\n",edf.length)

print("Dates:\n",edf.VORGANGSZE)

def yrs(x):
    return dt.datetime.strptime(x,"%Y-%m-%dT%H:%M:%S").date().year

edf["year"] = edf.VORGANGSZE.apply(yrs)
print("Years:\n",edf.year)

edf.to_file("edf.geojson")

png = "tracks.png"
print(f"Plotting to {png}")

# plot, color by years
years = gp.np.sort(edf.year.unique())
print("Years:\n",years)

def colorFader(c1,c2,mix=0): #fade (linear interpolate) from color c1 (at mix=0) to c2 (mix=1)
    c1=gp.np.array(cls.to_rgb(c1))
    c2=gp.np.array(cls.to_rgb(c2))
    return cls.to_hex((1-mix)*c1 + mix*c2)

colors = []
N = len(years)
for i in range(0,N):
    colors.append(colorFader("black","blue",i/N))

ys = [str(y) for y in years]
cmap = dict(zip(ys,colors))

# https://stackoverflow.com/questions/38882233/geopandas-matplotlib-plot-custom-colors
def colorize(x):
    y = gp.np.array(years)
    #print(x,cols)
    idx = gp.np.where(y == x)[0][0]
    return idx

edf["color"] = edf.year.apply(colorize)

colorList = [cls.hex2color(x) for x in colors]

colorMap = cls.LinearSegmentedColormap.from_list(
    'edfMap', colorList, N=len(colorList))



# https://geopandas.org/en/stable/docs/user_guide/mapping.html
#

# bounds 
minBounds = edf.geometry.bounds.min()
maxBounds = edf.geometry.bounds.max()

width = maxBounds.maxx - minBounds.minx
height = maxBounds.maxy - minBounds.miny

bounds = [minBounds.minx - int(width*.03),
          minBounds.miny - int(height*.03),
          maxBounds.maxx + int(width*.03),
          maxBounds.maxy + int(height*.03)]

# text pos
tx = bounds[0] + int(width * .02)
ty = bounds[1] - int(height * .08)

fig, ax = plt.subplots(1, 1)
fig.set_dpi(96)
fig.set_figwidth(10)
fig.set_figheight(10)
ax.set_xlim(bounds[0],bounds[2])
ax.set_ylim(bounds[1],bounds[3])

# changing year to color gives same coloring as in video
edf.plot("year",
         ax = ax,
        cmap = colorMap,
        legend=True,
        legend_kwds={
            'label': "Year",
            'orientation': "horizontal"
            },
        figsize=(10,10))

# osm providers: ['Mapnik', 'DE', 'CH', 'France', 'HOT', 'BZH', 'BlackAndWhite']
# Mapnik and DE work
# Stamen: ['Toner', 'TonerBackground', 'TonerHybrid', 'TonerLines', 'TonerLabels', 'TonerLite', 'Watercolor', 'Terrain', 'TerrainBackground', 'TerrainLabels', 'TopOSMRelief', 'TopOSMFeatures']

# provider list: cx.providers
# cx.add_basemap(ax, crs=edf.crs,source=cx.providers.OpenStreetMap.DE)

if loadMap:
    basemap = cx.providers.OpenStreetMap.Mapnik
    cx.add_basemap(ax, crs=edf.crs,source=basemap)

ax.axis("off")
ax.text(tx,ty ,str(years[0]) + " - " + str(years[-1]),
        backgroundcolor='0.75',alpha=.5,
        fontsize=24)
plt.title('Radwege Karlsruhe')
ax.figure.savefig(png)

plt.show()

#sys.exit()


#####

fig, ax = plt.subplots(1, 1)
fig.set_dpi(96)
fig.set_figwidth(10)
fig.set_figheight(10)
ax.set_xlim(bounds[0],bounds[2])
ax.set_ylim(bounds[1],bounds[3])
ax.axis("off")

ln, = plt.plot([], [], 'ro')

# we start with 1980-2007 to skip gap
def init():
    print("init start")
    color = cmap[str(years[0])]
    print("init color",color)
    current = edf[edf.year <= years[1]]
    length = current.length.sum() / 1000
    tracks = len(edf[edf.year  <= years[1]])
    current.plot(
        color=color,
        ax = ax,
        figsize=(10,10))

    ## lt = f"Bis {years[1]}: {length:.2f} km"
    lt = f"Bis {years[1]}: {tracks} Wege. {format_decimal(length, format='#.#', locale='de_DE')} km"

    ax.text(tx,ty,lt, fontsize=24)
    if loadMap:
        cx.add_basemap(ax, crs=edf.crs, source=basemap)
    plt.title('Radwege Karlsruhe')
    
    print("init done")
    return ln, 
    

def update(frame):
    #color = cls.hex2color(cmap[str(frame)])
    color = cmap[str(frame)]
    print("update start",frame,color)
    current = edf[edf.year  == frame]
    length = edf[edf.year  <= frame].length.sum() / 1000
    tracks = len(edf[edf.year  <= frame])
    #current.length.sum()
    current.plot(
        color=color,
        ax = ax,
        figsize=(10,10))

    #lt = f"{frame}: {tracks} Wege, {length:.2f} km      "
    lt = f"{frame}: {tracks} Wege. {format_decimal(length, format='#.#', locale='de_DE')} km     "
    ax.text(tx,ty,lt,
        backgroundcolor='0.8',alpha=1,
        fontsize=24)
    print("update done ")
    return ln,

ani = FuncAnimation(fig, update, frames=years[1:],
                    init_func=init, interval = 1500, blit=True)

ani.save("tracks.mp4")

# see also https://matplotlib.org/stable/gallery/animation/dynamic_image.html
